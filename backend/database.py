import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Generator

DB_PATH = os.getenv("DATABASE_URL", "/tmp/svcii.db")


def get_db_path() -> str:
    return DB_PATH


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS companies (
                ticker TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                sector TEXT,
                industry TEXT,
                market_cap_b REAL,
                msci_esg_rating TEXT,
                sp500 INTEGER DEFAULT 1,
                has_esg_report INTEGER DEFAULT 0,
                esg_report_year INTEGER,
                facility_count INTEGER
            );

            CREATE TABLE IF NOT EXISTS svcii_scores (
                ticker TEXT PRIMARY KEY,
                e_score REAL,
                s_score REAL,
                svcii REAL,
                classification TEXT,
                methodology TEXT,
                last_updated TEXT,
                data_vintage TEXT,
                e_trend_direction REAL,
                e_magnitude_score REAL,
                e_temporal_score REAL,
                e_disclosure_score REAL,
                divergence_pct REAL,
                metric_type TEXT,
                s_land_integrity REAL,
                s_community_prosperity REAL,
                s_supply_chain REAL,
                FOREIGN KEY (ticker) REFERENCES companies(ticker)
            );

            CREATE TABLE IF NOT EXISTS esg_claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT,
                claim_text TEXT,
                category TEXT,
                subcategory TEXT,
                metric_type TEXT,
                baseline_year INTEGER,
                target_year INTEGER,
                magnitude_pct REAL,
                source_doc TEXT,
                page_number INTEGER,
                FOREIGN KEY (ticker) REFERENCES companies(ticker)
            );

            CREATE TABLE IF NOT EXISTS facilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT,
                facility_name TEXT,
                latitude REAL,
                longitude REAL,
                operation_type TEXT,
                country TEXT,
                region TEXT,
                xch4_value REAL,
                xch4_trend REAL,
                ntl_value REAL,
                FOREIGN KEY (ticker) REFERENCES companies(ticker)
            );

            CREATE TABLE IF NOT EXISTS satellite_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT,
                facility_id INTEGER,
                source TEXT,
                metric TEXT,
                value REAL,
                unit TEXT,
                period_start TEXT,
                period_end TEXT,
                latitude REAL,
                longitude REAL,
                FOREIGN KEY (ticker) REFERENCES companies(ticker),
                FOREIGN KEY (facility_id) REFERENCES facilities(id)
            );
        """)


def seed_if_empty() -> None:
    """
    DEMO DATA ONLY.

    Seeds illustrative placeholder companies/scores so the API has
    something to return on a fresh deploy before the pipeline has run.
    None of these numbers come from satellite or ESG-report data — they
    are NOT real findings. Run pipeline/05_populate_database.py to
    replace this with real pipeline output (it clears these tables first).
    """
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
        if count > 0:
            return

    now = datetime.now(timezone.utc).isoformat()

    # DEMO DATA — illustrative only, not real findings.
    companies = [
        ("XOM", "ExxonMobil", "Energy", "Oil & Gas", 450.0, "CCC", 1, 1, 2023, 1),
        ("CVX", "Chevron", "Energy", "Oil & Gas", 290.0, "B", 1, 1, 2023, 1),
        ("COP", "ConocoPhillips", "Energy", "Oil & Gas", 140.0, "BB", 1, 1, 2023, 1),
        ("MSFT", "Microsoft", "Technology", "Software", 3100.0, "AAA", 1, 1, 2023, 1),
        ("NEE", "NextEra Energy", "Utilities", "Renewable Utilities", 120.0, "A", 1, 1, 2023, 1),
    ]

    scores = [
        ("XOM", 28.0, 37.0, 31.5, "MAJOR DIVERGENCE", "60% Environmental / 40% Social", now, "DEMO",
         -1, 5.0, 10.0, 5.0, 22.0, "intensity", 40.0, 35.0, 50.0),
        ("CVX", 30.0, 38.0, 33.2, "MAJOR DIVERGENCE", "60% Environmental / 40% Social", now, "DEMO",
         -1, 8.0, 10.0, 5.0, 18.0, "intensity", 42.0, 36.0, 50.0),
        ("COP", 35.0, 40.0, 37.0, "MAJOR DIVERGENCE", "60% Environmental / 40% Social", now, "DEMO",
         -1, 10.0, 12.0, 5.0, 15.0, "intensity", 45.0, 38.0, 50.0),
        ("MSFT", 91.0, 84.0, 88.2, "CONSISTENT", "60% Environmental / 40% Social", now, "DEMO",
         1, 28.0, 18.0, 20.0, 3.0, "absolute", 86.0, 82.0, 50.0),
        ("NEE", 85.0, 80.0, 83.0, "CONSISTENT", "60% Environmental / 40% Social", now, "DEMO",
         1, 26.0, 17.0, 20.0, 4.0, "absolute", 82.0, 78.0, 50.0),
    ]

    with get_connection() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO companies VALUES (?,?,?,?,?,?,?,?,?,?)", companies
        )
        conn.executemany(
            """INSERT OR IGNORE INTO svcii_scores VALUES
               (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            scores,
        )


def clear_all() -> None:
    """Used by the real pipeline before loading real scores."""
    with get_connection() as conn:
        conn.executescript("""
            DELETE FROM satellite_readings;
            DELETE FROM facilities;
            DELETE FROM esg_claims;
            DELETE FROM svcii_scores;
            DELETE FROM companies;
        """)


def get_all_companies(
    sector: str | None = None,
    classification: str | None = None,
    metric_type: str | None = None,
    min_score: float | None = None,
    max_score: float | None = None,
):
    query = """
        SELECT c.ticker, c.name, c.sector, c.industry, c.market_cap_b,
               c.msci_esg_rating, s.svcii, s.e_score, s.s_score,
               s.classification, s.metric_type
        FROM companies c
        LEFT JOIN svcii_scores s ON c.ticker = s.ticker
        WHERE 1=1
    """
    params: list = []
    if sector:
        query += " AND c.sector = ?"
        params.append(sector)
    if classification:
        query += " AND s.classification = ?"
        params.append(classification)
    if metric_type:
        query += " AND s.metric_type = ?"
        params.append(metric_type)
    if min_score is not None:
        query += " AND s.svcii >= ?"
        params.append(min_score)
    if max_score is not None:
        query += " AND s.svcii <= ?"
        params.append(max_score)
    query += " ORDER BY s.svcii DESC"

    with get_connection() as conn:
        return conn.execute(query, params).fetchall()


def get_company(ticker: str):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM companies WHERE ticker = ?", (ticker.upper(),)
        ).fetchone()


def get_score(ticker: str):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM svcii_scores WHERE ticker = ?", (ticker.upper(),)
        ).fetchone()


def get_all_scores():
    with get_connection() as conn:
        return conn.execute("SELECT * FROM svcii_scores ORDER BY svcii DESC").fetchall()


def get_claims(ticker: str):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM esg_claims WHERE ticker = ? ORDER BY id", (ticker.upper(),)
        ).fetchall()


def get_facilities(ticker: str):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM facilities WHERE ticker = ?", (ticker.upper(),)
        ).fetchall()


def get_satellite_readings(ticker: str):
    with get_connection() as conn:
        return conn.execute(
            """SELECT * FROM satellite_readings WHERE ticker = ?
               ORDER BY period_end""",
            (ticker.upper(),),
        ).fetchall()


def get_risk_assessment(ticker: str):
    """
    Derives a regulatory-risk note from the already-computed score and
    classification. Not a fabricated number — a deterministic mapping
    of SVCII classification + divergence magnitude onto a risk tier.
    """
    ticker = ticker.upper()
    with get_connection() as conn:
        score = conn.execute(
            "SELECT * FROM svcii_scores WHERE ticker = ?", (ticker,)
        ).fetchone()
        facilities = conn.execute(
            "SELECT * FROM facilities WHERE ticker = ?", (ticker,)
        ).fetchall()

    if score is None:
        return None

    classification = score["classification"]
    divergence = score["divergence_pct"] or 0.0

    if classification == "MAJOR DIVERGENCE":
        risk = "CRITICAL" if divergence >= 25 else "HIGH"
    elif classification == "WARRANTS INVESTIGATION":
        risk = "MEDIUM"
    elif classification == "INCONCLUSIVE":
        risk = "MEDIUM" if divergence >= 15 else "LOW"
    else:
        risk = "LOW"

    risk_factors = []
    if classification in ("MAJOR DIVERGENCE", "WARRANTS INVESTIGATION"):
        risk_factors.append(
            f"Satellite-observed emissions trend diverges from disclosed claims by "
            f"{divergence:.1f} percentage points."
        )
    if score["metric_type"] == "intensity":
        risk_factors.append(
            "Primary disclosure is intensity-based, which can mask absolute "
            "emissions growth even when claimed reductions are accurate."
        )
    if score["e_trend_direction"] is not None and score["e_trend_direction"] > 0 and classification != "CONSISTENT":
        risk_factors.append(
            "Facility-level methane readings show an increasing trend over the "
            "observed period."
        )
    if not facilities:
        risk_factors.append(
            "No facility coordinates on file — satellite verification coverage "
            "is limited for this company."
        )
    if not risk_factors:
        risk_factors.append(
            "No material divergence detected between disclosed claims and "
            "satellite-observed data over the covered period."
        )

    if risk in ("CRITICAL", "HIGH"):
        exposure_note = (
            "Funds marketed as ESG/sustainable that hold this company should "
            "disclose the basis for that classification; satellite data suggests "
            "a material gap between claims and observed activity."
        )
    elif risk == "MEDIUM":
        exposure_note = (
            "Mixed signal — worth flagging in fund-level ESG due diligence but "
            "not conclusive on its own."
        )
    else:
        exposure_note = (
            "No material exposure flagged based on currently available satellite data."
        )

    if score["divergence_pct"] is not None:
        sat_summary = (
            f"Satellite-observed change diverges from the disclosed claim by "
            f"{score['divergence_pct']:.1f} percentage points "
            f"(metric type: {score['metric_type'] or 'unknown'})."
        )
    else:
        sat_summary = "Insufficient satellite data to compute a divergence figure."

    return {
        "ticker": ticker,
        "regulatory_risk": risk,
        "risk_factors": risk_factors,
        "esg_fund_exposure_note": exposure_note,
        "satellite_vs_claim_summary": sat_summary,
    }


def get_leaderboard(n: int = 10):
    with get_connection() as conn:
        top = conn.execute("""
            SELECT c.ticker, c.name, c.sector, s.svcii, s.classification
            FROM companies c JOIN svcii_scores s ON c.ticker = s.ticker
            WHERE s.svcii IS NOT NULL ORDER BY s.svcii DESC LIMIT ?
        """, (n,)).fetchall()
        bottom = conn.execute("""
            SELECT c.ticker, c.name, c.sector, s.svcii, s.classification
            FROM companies c JOIN svcii_scores s ON c.ticker = s.ticker
            WHERE s.svcii IS NOT NULL ORDER BY s.svcii ASC LIMIT ?
        """, (n,)).fetchall()
    return top, bottom


def get_sector_scores():
    with get_connection() as conn:
        return conn.execute("""
            SELECT c.sector,
                   AVG(s.svcii) as avg_svcii,
                   AVG(s.e_score) as avg_e_score,
                   AVG(s.s_score) as avg_s_score,
                   COUNT(c.ticker) as company_count,
                   SUM(CASE WHEN s.classification = 'CONSISTENT' THEN 1 ELSE 0 END) as consistent_count,
                   SUM(CASE WHEN s.classification = 'MAJOR DIVERGENCE' THEN 1 ELSE 0 END) as divergent_count
            FROM companies c
            JOIN svcii_scores s ON c.ticker = s.ticker
            WHERE c.sector IS NOT NULL AND s.svcii IS NOT NULL
            GROUP BY c.sector ORDER BY avg_svcii DESC
        """).fetchall()


def get_score_distribution():
    buckets = [
        (0, 40, "MAJOR DIVERGENCE"),
        (40, 60, "WARRANTS INVESTIGATION"),
        (60, 80, "INCONCLUSIVE"),
        (80, 100.01, "CONSISTENT"),
    ]
    with get_connection() as conn:
        result = []
        for start, end, label in buckets:
            count = conn.execute(
                "SELECT COUNT(*) FROM svcii_scores WHERE svcii >= ? AND svcii < ?",
                (start, end),
            ).fetchone()[0]
            result.append(
                {"bucket_start": start, "bucket_end": min(end, 100), "count": count, "label": label}
            )
        return result


def search_companies(q: str):
    pattern = f"%{q}%"
    with get_connection() as conn:
        return conn.execute("""
            SELECT c.ticker, c.name, c.sector, s.svcii, s.classification
            FROM companies c
            LEFT JOIN svcii_scores s ON c.ticker = s.ticker
            WHERE c.ticker LIKE ? OR c.name LIKE ?
            LIMIT 10
        """, (pattern, pattern)).fetchall()


def get_stats() -> dict:
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
        scored = conn.execute(
            "SELECT COUNT(*), AVG(svcii) FROM svcii_scores WHERE svcii IS NOT NULL"
        ).fetchone()
        claims_count = conn.execute("SELECT COUNT(*) FROM esg_claims").fetchone()[0]
        class_counts = conn.execute("""
            SELECT classification, COUNT(*) as cnt
            FROM svcii_scores WHERE classification IS NOT NULL
            GROUP BY classification
        """).fetchall()
    class_map = {r["classification"]: r["cnt"] for r in class_counts}
    total_scored = scored[0] or 1
    major_div = class_map.get("MAJOR DIVERGENCE", 0)
    return {
        "total_companies": total,
        "avg_svcii": round(scored[1] or 0, 1),
        "major_divergence_pct": round(major_div / total_scored * 100, 1),
        "consistent_count": class_map.get("CONSISTENT", 0),
        "inconclusive_count": class_map.get("INCONCLUSIVE", 0),
        "warrants_investigation_count": class_map.get("WARRANTS INVESTIGATION", 0),
        "major_divergence_count": major_div,
        "claims_verified": claims_count,
    }
