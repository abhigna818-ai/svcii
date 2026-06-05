#!/usr/bin/env python3
"""
Fetch facility coordinates from Global Energy Monitor (GEM) wiki.
GEM tracks oil, gas, coal, and power plant locations globally.
Source: https://www.gem.wiki — download facility datasets from GEM's data portal.

For offline/demo use, reads from data/facilities.csv if GEM API unavailable.
Usage: python 02_fetch_facilities.py [--db ../data/svcii.db]
"""
import sys
import csv
import requests
from utils import get_conn, log, ensure_data_dir

DB_PATH = sys.argv[sys.argv.index("--db") + 1] if "--db" in sys.argv else "../data/svcii.db"

GEM_OIL_GAS_CSV = "https://globalenergymonitor.org/wp-content/uploads/2023/07/GlobalOilInfrastructureTracker-July2023.csv"


def fetch_gem_csv(url: str) -> list[dict]:
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        lines = resp.text.splitlines()
        return list(csv.DictReader(lines))
    except Exception as e:
        log.warning(f"GEM download failed: {e}")
        return []


def load_local_csv(path: str) -> list[dict]:
    try:
        with open(path) as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return []


def main():
    data_dir = ensure_data_dir()
    rows = fetch_gem_csv(GEM_OIL_GAS_CSV) or load_local_csv(str(data_dir / "facilities.csv"))
    if not rows:
        log.warning("No facility data. Using seed data from 09_seed_demo_data.py instead.")
        return

    conn = get_conn(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT ticker FROM companies")
    known = {r[0] for r in cur.fetchall()}

    inserted = 0
    for r in rows:
        ticker = r.get("ticker", r.get("Company Ticker", "")).strip().upper()
        if ticker not in known:
            continue
        try:
            lat = float(r.get("latitude", r.get("Latitude", 0)))
            lon = float(r.get("longitude", r.get("Longitude", 0)))
        except (ValueError, TypeError):
            continue
        cur.execute(
            """INSERT OR IGNORE INTO facilities
               (ticker, facility_name, latitude, longitude, operation_type, country, region)
               VALUES (?,?,?,?,?,?,?)""",
            (
                ticker,
                r.get("facility_name", r.get("Facility Name", "Unknown")),
                lat, lon,
                r.get("operation_type", r.get("Type", "")),
                r.get("country", r.get("Country", "")),
                r.get("region", r.get("Region", "")),
            ),
        )
        inserted += 1

    conn.commit()
    conn.close()
    log.info(f"Inserted {inserted} facilities.")


if __name__ == "__main__":
    main()
