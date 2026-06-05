#!/usr/bin/env python3
"""
Download and parse EPA GHGRP oil & gas facility methane emissions.
Source: https://www.epa.gov/ghgreporting/ghg-reporting-program-data-sets
Download ogdataset.zip → extract → parse facility-level CH4 data.

Usage: python 03_fetch_epa_ghgrp.py [--db ../data/svcii.db] [--year 2022]
"""
import sys
import os
import csv
import zipfile
import io
import requests
from utils import get_conn, log, ensure_data_dir

DB_PATH   = sys.argv[sys.argv.index("--db")   + 1] if "--db"   in sys.argv else "../data/svcii.db"
YEAR      = sys.argv[sys.argv.index("--year") + 1] if "--year" in sys.argv else "2022"

EPA_ZIP_URL = f"https://www.epa.gov/system/files/other-files/2023-10/flight_{YEAR}_ogdataset.zip"


def download_epa(url: str, data_dir) -> list[dict]:
    log.info(f"Downloading EPA GHGRP dataset from {url}")
    try:
        resp = requests.get(url, timeout=120, stream=True)
        resp.raise_for_status()
        content = b"".join(resp.iter_content(chunk_size=1024 * 1024))
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            # Look for the facility emissions CSV
            csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv") and "facilit" in n.lower()]
            if not csv_names:
                csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if not csv_names:
                log.error("No CSV found in EPA zip")
                return []
            with zf.open(csv_names[0]) as f:
                reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
                return list(reader)
    except Exception as e:
        log.warning(f"EPA download failed: {e}")
        return []


def match_ticker(facility_name: str, parent_company: str, known_companies: dict) -> str | None:
    """Fuzzy match facility parent company to ticker."""
    name_lower = (parent_company or facility_name or "").lower()
    for ticker, company_name in known_companies.items():
        if any(w in name_lower for w in company_name.lower().split()[:2]):
            return ticker
    return None


def main():
    data_dir = ensure_data_dir()
    rows = download_epa(EPA_ZIP_URL, data_dir)
    if not rows:
        log.warning("No EPA data. Skipping — satellite_readings will use seeded data.")
        return

    conn = get_conn(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT ticker, name FROM companies")
    known = {r[0]: r[1] for r in cur.fetchall()}
    cur.execute("SELECT id, ticker, facility_name FROM facilities")
    facilities = {(r[1], r[2]): r[0] for r in cur.fetchall()}

    inserted = 0
    for row in rows:
        # EPA GHGRP column names vary by year; try multiple
        ch4_val_str = row.get("CH4_QUANTITY", row.get("Methane (metric tons CO2e)", ""))
        try:
            ch4_val = float(ch4_val_str.replace(",", "")) if ch4_val_str else None
        except ValueError:
            ch4_val = None
        if ch4_val is None:
            continue

        parent = row.get("PARENT_COMPANY_NAME", row.get("Reporting Company", ""))
        ticker = match_ticker("", parent, known)
        if not ticker:
            continue

        facility_name = row.get("FACILITY_NAME", row.get("Facility Name", "Unknown"))
        try:
            lat = float(row.get("LATITUDE", row.get("Latitude", 0)))
            lon = float(row.get("LONGITUDE", row.get("Longitude", 0)))
        except ValueError:
            lat = lon = 0.0

        # Upsert facility
        fac_key = (ticker, facility_name)
        if fac_key not in facilities:
            cur.execute(
                "INSERT INTO facilities (ticker, facility_name, latitude, longitude, operation_type, country, region) VALUES (?,?,?,?,?,?,?)",
                (ticker, facility_name, lat, lon, "Oil & Gas", "USA", ""),
            )
            facilities[fac_key] = cur.lastrowid

        fac_id = facilities[fac_key]
        cur.execute(
            "INSERT INTO satellite_readings (facility_id, data_type, period_start, period_end, value, unit, source) VALUES (?,?,?,?,?,?,?)",
            (fac_id, "epa_ghgrp_ch4", f"{YEAR}-01-01", f"{YEAR}-12-31",
             ch4_val, "metric_tons_CO2e", "EPA GHGRP"),
        )
        inserted += 1

    conn.commit()
    conn.close()
    log.info(f"Inserted {inserted} EPA GHGRP methane readings.")


if __name__ == "__main__":
    main()
