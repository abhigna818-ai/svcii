#!/usr/bin/env python3
"""
Compute SVCII scores for all companies with sufficient data and update svcii_scores table.
Run after all data ingestion scripts.

Usage: python 08_compute_scores.py [--db ../data/svcii.db] [--ticker XOM]
"""
import sys
import os
from datetime import datetime, UTC

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend"))
from utils import get_conn, log

DB_PATH = sys.argv[sys.argv.index("--db")     + 1] if "--db"     in sys.argv else "../data/svcii.db"
ONLY    = sys.argv[sys.argv.index("--ticker") + 1] if "--ticker" in sys.argv else None


def get_primary_claim(cur, ticker: str, subcategory: str = "methane") -> dict | None:
    cur.execute("""
        SELECT magnitude_pct, metric_type, baseline_year, target_year
        FROM esg_claims
        WHERE ticker = ? AND subcategory = ? AND magnitude_pct IS NOT NULL
        ORDER BY ABS(magnitude_pct) DESC LIMIT 1
    """, (ticker, subcategory))
    row = cur.fetchone()
    return dict(row) if row else None


def get_satellite_trend(cur, fac_ids: list[int], data_type: str = "tropomi_xch4") -> dict:
    if not fac_ids:
        return {"direction": 0, "pct_change": 0.0, "readings": []}

    placeholders = ",".join("?" * len(fac_ids))
    cur.execute(f"""
        SELECT period_end, AVG(value) as avg_val
        FROM satellite_readings
        WHERE facility_id IN ({placeholders}) AND data_type = ?
        GROUP BY period_end
        ORDER BY period_end
    """, (*fac_ids, data_type))
    rows = cur.fetchall()
    if len(rows) < 2:
        return {"direction": 0, "pct_change": 0.0, "readings": [dict(r) for r in rows]}

    first = rows[0]["avg_val"]
    last = rows[-1]["avg_val"]
    pct_change = ((last - first) / first * 100) if first else 0.0
    direction = -1 if pct_change < -1.0 else (1 if pct_change > 1.0 else 0)
    return {
        "direction": direction,
        "pct_change": round(pct_change, 2),
        "readings": [{"period_end": r["period_end"], "value": r["avg_val"]} for r in rows],
    }


def get_land_score(cur, fac_ids: list[int]) -> float | None:
    if not fac_ids:
        return None
    placeholders = ",".join("?" * len(fac_ids))
    cur.execute(f"""
        SELECT AVG(value) FROM satellite_readings
        WHERE facility_id IN ({placeholders}) AND data_type = 'worldcover_ndvi'
    """, fac_ids)
    row = cur.fetchone()
    return round(row[0], 1) if row[0] is not None else None


def get_ntl_score(cur, fac_ids: list[int]) -> float | None:
    if not fac_ids:
        return None
    placeholders = ",".join("?" * len(fac_ids))
    cur.execute(f"""
        SELECT value FROM satellite_readings
        WHERE facility_id IN ({placeholders}) AND data_type = 'viirs_ntl'
        ORDER BY period_end DESC LIMIT 1
    """, fac_ids)
    row = cur.fetchone()
    if row is None:
        return None
    # Normalize NTL: 0–5 nW = low (score 40-60), 5-50 = high (60-90)
    ntl = row[0]
    score = min(100, max(0, 40 + ntl * 1.0))
    return round(score, 1)


def compute_temporal_consistency(readings: list[dict]) -> float:
    if len(readings) < 3:
        return 10.0
    values = [r["value"] for r in readings]
    direction_changes = sum(
        1 for i in range(1, len(values) - 1)
        if (values[i] - values[i-1]) * (values[i+1] - values[i]) < 0
    )
    max_changes = len(values) - 2
    ratio = 1.0 - (direction_changes / max_changes) if max_changes > 0 else 1.0
    return round(ratio * 20, 1)


def compute_and_store(cur, ticker: str) -> bool:
    claim = get_primary_claim(cur, ticker, "methane")
    if not claim:
        log.warning(f"{ticker}: no quantified methane claim found, skipping")
        return False

    cur.execute("SELECT id FROM facilities WHERE ticker = ?", (ticker,))
    fac_ids = [r["id"] for r in cur.fetchall()]

    sat = get_satellite_trend(cur, fac_ids)
    temporal_score = compute_temporal_consistency(sat["readings"])

    mag_pct = claim["magnitude_pct"]
    divergence = abs(mag_pct - sat["pct_change"])
    magnitude_score = max(0.0, 30.0 - divergence * 0.6)

    claimed_dir = -1 if mag_pct < 0 else 1
    if claimed_dir == sat["direction"]:
        trend_score = 40.0
    elif sat["direction"] == 0:
        trend_score = 20.0
    else:
        trend_score = 0.0

    metric_type = claim["metric_type"]
    disclosure_score = 10.0 if metric_type == "absolute" else 0.0

    e_score = trend_score + magnitude_score + temporal_score + disclosure_score
    if metric_type == "intensity":
        e_score = max(0.0, e_score - 10.0)
    e_score = round(min(100.0, max(0.0, e_score)), 1)

    # S score
    cur.execute("""
        SELECT subcategory, COUNT(*) as cnt FROM esg_claims
        WHERE ticker = ? AND category = 'social' GROUP BY subcategory
    """, (ticker,))
    social_counts = {r["subcategory"]: r["cnt"] for r in cur.fetchall()}
    land_c = social_counts.get("land", 0)
    comm_c = social_counts.get("community", 0)
    supply_c = social_counts.get("supply_chain", 0)
    total_s = land_c + comm_c + supply_c

    s_land = get_land_score(cur, fac_ids)
    s_comm = get_ntl_score(cur, fac_ids)
    s_supply = (s_land + s_comm) / 2 if s_land and s_comm else None

    s_score: float | None = None
    if total_s > 0 and s_land is not None:
        w1 = land_c / total_s
        w2 = comm_c / total_s
        w3 = supply_c / total_s
        lis = s_land or 50.0
        cps = s_comm or 50.0
        slus = s_supply or 50.0
        s_score = round(w1 * lis + w2 * cps + w3 * slus, 1)

    if s_score is not None:
        svcii = round(0.6 * e_score + 0.4 * s_score, 1)
        methodology = "60% Environmental / 40% Social"
    else:
        svcii = e_score
        methodology = "E-only (no verifiable social claims)"

    if svcii >= 80:
        classification = "CONSISTENT"
    elif svcii >= 60:
        classification = "INCONCLUSIVE"
    elif svcii >= 40:
        classification = "WARRANTS INVESTIGATION"
    else:
        classification = "MAJOR DIVERGENCE"

    cur.execute("""
        INSERT OR REPLACE INTO svcii_scores
        (ticker, svcii, e_score, s_score, e_trend_direction, e_magnitude_score,
         e_temporal_score, e_disclosure_score, s_land_integrity, s_community_prosperity,
         s_supply_chain, classification, metric_type, divergence_pct,
         methodology, last_updated, data_vintage)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        ticker, svcii, e_score, s_score,
        sat["direction"], round(magnitude_score, 1), temporal_score, disclosure_score,
        s_land, s_comm, s_supply,
        classification, metric_type, round(divergence, 2),
        methodology, datetime.now(UTC).isoformat(), "2023–2024",
    ))
    log.info(f"{ticker}: SVCII={svcii} ({classification})")
    return True


def main():
    conn = get_conn(DB_PATH)
    cur = conn.cursor()

    if ONLY:
        tickers = [ONLY.upper()]
    else:
        cur.execute("SELECT ticker FROM companies")
        tickers = [r["ticker"] for r in cur.fetchall()]

    computed = 0
    for ticker in tickers:
        if compute_and_store(cur, ticker):
            computed += 1

    conn.commit()
    conn.close()
    log.info(f"Computed SVCII scores for {computed}/{len(tickers)} companies.")


if __name__ == "__main__":
    main()
