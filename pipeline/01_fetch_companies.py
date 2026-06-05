#!/usr/bin/env python3
"""
Fetch S&P 500 company list and populate the companies table.
Source: Wikipedia S&P 500 list (parsed via requests + BeautifulSoup),
        supplemented by data/sp500_companies.csv.

Usage: python 01_fetch_companies.py [--db ../data/svcii.db]
"""
import sys
import csv
import requests
from utils import get_conn, log, ensure_data_dir

DB_PATH = sys.argv[sys.argv.index("--db") + 1] if "--db" in sys.argv else "../data/svcii.db"


def fetch_sp500_wikipedia() -> list[dict]:
    """Parse S&P 500 list from Wikipedia."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    try:
        from bs4 import BeautifulSoup
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", {"id": "constituents"})
        rows = []
        headers = [th.text.strip() for th in table.find_all("th")]
        for tr in table.find_all("tr")[1:]:
            cells = [td.text.strip() for td in tr.find_all("td")]
            if cells:
                rows.append(dict(zip(headers, cells)))
        return rows
    except Exception as e:
        log.warning(f"Wikipedia fetch failed: {e} — falling back to CSV")
        return []


def load_from_csv(path: str) -> list[dict]:
    try:
        with open(path) as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return []


def main():
    data_dir = ensure_data_dir()
    rows = fetch_sp500_wikipedia() or load_from_csv(str(data_dir / "sp500_companies.csv"))
    if not rows:
        log.error("No company data found. Run 09_seed_demo_data.py for demo data.")
        sys.exit(1)

    conn = get_conn(DB_PATH)
    inserted = 0
    for r in rows:
        ticker = r.get("Symbol", r.get("ticker", "")).strip()
        name = r.get("Security", r.get("name", "")).strip()
        sector = r.get("GICS Sector", r.get("sector", "")).strip()
        industry = r.get("GICS Sub-Industry", r.get("industry", "")).strip()
        if not ticker or not name:
            continue
        conn.execute(
            """INSERT OR IGNORE INTO companies (ticker, name, sector, industry, sp500)
               VALUES (?, ?, ?, ?, 1)""",
            (ticker, name, sector or None, industry or None),
        )
        inserted += 1

    conn.commit()
    conn.close()
    log.info(f"Inserted/updated {inserted} companies.")


if __name__ == "__main__":
    main()
