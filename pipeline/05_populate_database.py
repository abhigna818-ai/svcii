#!/usr/bin/env python3
"""
Load real pipeline output (claims, satellite readings, scores) into the
SQLite database, replacing the demo seed data entirely.

Usage:
    python 05_populate_database.py [--db /path/to/svcii.db]

Run order: 01_fetch_esg_claims.py -> 02_fetch_satellite_methane.py ->
03_fetch_nighttime_lights.py -> 04_score_companies.py -> this script.
"""
import csv
import json
import sqlite3
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = sys.argv[sys.argv.index("--db") + 1] if "--db" in sys.argv else "/tmp/svcii.db"

FACILITIES = {
    "XOM": {"facility_name": "Permian Basin", "latitude": 31.5, "longitude": -103.5,
            "operation_type": "Oil & Gas Production", "country": "USA", "region": "Texas/New Mexico"},
    "CVX": {"facility_name": "Permian Basin", "latitude": 31.8, "longitude": -102.9,
            "operation_type": "Oil & Gas Production", "country": "USA", "region": "Texas/New Mexico"},
    "COP": {"facility_name": "Eagle Ford", "latitude": 28.8, "longitude": -99.2,
            "operation_type": "Oil & Gas Production", "country": "USA", "region": "Texas"},
    "NEE": {"facility_name": "Florida Power & Light service territory", "latitude": 26.4, "longitude": -80.1,
            "operation_type": "Electric Utility", "country": "USA", "region": "Florida"},
}


def load_companies_csv() -> dict[str, dict]:
    out = {}
    csv_path = DATA_DIR / "sp500_companies.csv"
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            out[row["ticker"]] = row
    return out


def init_schema(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS companies (
            ticker TEXT PRIMARY KEY, name TEXT NOT NULL, sector TEXT, industry TEXT,
            market_cap_b REAL, msci_esg_rating TEXT, sp500 INTEGER DEFAULT 1,
            has_esg_report INTEGER DEFAULT 0, esg_report_year INTEGER, facility_count INTEGER
        );
        CREATE TABLE IF NOT EXISTS svcii_scores (
            ticker TEXT PRIMARY KEY, e_score REAL, s_score REAL, svcii REAL,
            classification TEXT, methodology TEXT, last_updated TEXT, data_vintage TEXT,
            e_trend_direction REAL, e_magnitude_score REAL, e_temporal_score REAL,
            e_disclosure_score REAL, divergence_pct REAL, metric_type TEXT,
            s_land_integrity REAL, s_community_prosperity REAL, s_supply_chain REAL,
            FOREIGN KEY (ticker) REFERENCES companies(ticker)
        );
        CREATE TABLE IF NOT EXISTS esg_claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ticker TEXT, claim_text TEXT, category TEXT,
            subcategory TEXT, metric_type TEXT, baseline_year INTEGER, target_year INTEGER,
            magnitude_pct REAL, source_doc TEXT, page_number INTEGER,
            FOREIGN KEY (ticker) REFERENCES companies(ticker)
        );
        CREATE TABLE IF NOT EXISTS facilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ticker TEXT, facility_name TEXT,
            latitude REAL, longitude REAL, operation_type TEXT, country TEXT, region TEXT,
            xch4_value REAL, xch4_trend REAL, ntl_value REAL,
            FOREIGN KEY (ticker) REFERENCES companies(ticker)
        );
        CREATE TABLE IF NOT EXISTS satellite_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ticker TEXT, facility_id INTEGER, source TEXT,
            metric TEXT, value REAL, unit TEXT, period_start TEXT, period_end TEXT,
            latitude REAL, longitude REAL,
            FOREIGN KEY (ticker) REFERENCES companies(ticker),
            FOREIGN KEY (facility_id) REFERENCES facilities(id)
        );
    """)


def clear_all(conn: sqlite3.Connection):
    conn.executescript("""
        DELETE FROM satellite_readings;
        DELETE FROM facilities;
        DELETE FROM esg_claims;
        DELETE FROM svcii_scores;
        DELETE FROM companies;
    """)


def main():
    scores_path = DATA_DIR / "scores" / "final_scores.json"
    if not scores_path.exists():
        print(f"ERROR: {scores_path} not found. Run 04_score_companies.py first.")
        sys.exit(1)

    scores = json.loads(scores_path.read_text())
    if not scores:
        print("ERROR: final_scores.json is empty. Nothing to load.")
        sys.exit(1)

    companies_meta = load_companies_csv()
    methane = {r["ticker"]: r for r in json.loads(
        (DATA_DIR / "satellite" / "methane_readings.json").read_text()
    )} if (DATA_DIR / "satellite" / "methane_readings.json").exists() else {}
    lights = {r["ticker"]: r for r in json.loads(
        (DATA_DIR / "satellite" / "nighttime_lights.json").read_text()
    )} if (DATA_DIR / "satellite" / "nighttime_lights.json").exists() else {}

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    init_schema(conn)

    print("Clearing demo/seed data...")
    clear_all(conn)

    inserted_companies = inserted_scores = inserted_claims = inserted_facilities = inserted_readings = 0

    for score in scores:
        ticker = score["ticker"]
        meta = companies_meta.get(ticker, {})

        conn.execute(
            """INSERT INTO companies VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                ticker,
                meta.get("name", ticker),
                meta.get("sector"),
                meta.get("industry"),
                float(meta["market_cap_b"]) if meta.get("market_cap_b") else None,
                meta.get("msci_esg_rating"),
                1, 1, 2023,
                1 if ticker in FACILITIES else 0,
            ),
        )
        inserted_companies += 1

        e = score.get("e_score") or {}
        s = score.get("s_score") or {}
        e_comp = e.get("components", {})
        s_comp = s.get("components", {})

        conn.execute(
            """INSERT INTO svcii_scores VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                ticker,
                e.get("e_score"),
                s.get("s_score"),
                score["svcii"],
                score["classification"],
                score["methodology"],
                score["last_updated"],
                "2023 (pipeline run)",
                1 if e.get("metric_type") and e_comp.get("trend_direction_match", 0) > 0 else
                (-1 if e_comp.get("trend_direction_match", 0) == 0 and e.get("e_score") is not None else None),
                e_comp.get("magnitude_proportionality"),
                None,
                e_comp.get("disclosure_quality"),
                None,
                e.get("metric_type"),
                s_comp.get("land_integrity"),
                s_comp.get("community_prosperity"),
                s_comp.get("supply_chain"),
            ),
        )
        inserted_scores += 1

        claims_path = DATA_DIR / "claims" / f"{ticker}_claims.json"
        if claims_path.exists():
            claims_data = json.loads(claims_path.read_text())
            for c in claims_data.get("claims", []):
                conn.execute(
                    """INSERT INTO esg_claims
                       (ticker, claim_text, category, subcategory, metric_type,
                        baseline_year, target_year, magnitude_pct, source_doc, page_number)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (
                        ticker,
                        c.get("claim_text", "")[:500],
                        c.get("category"),
                        None,
                        c.get("metric_type"),
                        c.get("year"),
                        c.get("target_year"),
                        c.get("value"),
                        claims_data.get("source_url"),
                        None,
                    ),
                )
                inserted_claims += 1

        if ticker in FACILITIES:
            fac = FACILITIES[ticker]
            cur = conn.execute(
                """INSERT INTO facilities
                   (ticker, facility_name, latitude, longitude, operation_type, country, region)
                   VALUES (?,?,?,?,?,?,?)""",
                (ticker, fac["facility_name"], fac["latitude"], fac["longitude"],
                 fac["operation_type"], fac["country"], fac["region"]),
            )
            facility_id = cur.lastrowid
            inserted_facilities += 1

            m = methane.get(ticker)
            if m and m.get("status") in ("ok", "partial"):
                for year, value in m.get("ch4_tonnes_by_year", {}).items():
                    conn.execute(
                        """INSERT INTO satellite_readings
                           (ticker, facility_id, source, metric, value, unit,
                            period_start, period_end, latitude, longitude)
                           VALUES (?,?,?,?,?,?,?,?,?,?)""",
                        (ticker, facility_id, m.get("source"), "ch4_emissions", value, "tonnes/year",
                         f"{year}-01-01", f"{year}-12-31", fac["latitude"], fac["longitude"]),
                    )
                    inserted_readings += 1

    conn.commit()

    print("\n=== Database populated from real pipeline output ===")
    print(f"  companies:           {inserted_companies}")
    print(f"  svcii_scores:        {inserted_scores}")
    print(f"  esg_claims:          {inserted_claims}")
    print(f"  facilities:          {inserted_facilities}")
    print(f"  satellite_readings:  {inserted_readings}")
    print(f"  database path:       {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    main()
