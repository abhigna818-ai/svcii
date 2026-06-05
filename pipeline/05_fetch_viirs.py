#!/usr/bin/env python3
"""
Download NASA Black Marble VNP46A2 nighttime lights for facility regions.
Source: NASA LAADS DAAC — https://ladsweb.modaps.eosdis.nasa.gov/
Product: VNP46A2 (Daily/Monthly VIIRS Nighttime Lights)

Requires NASA Earthdata login. Set env vars:
  EARTHDATA_USER, EARTHDATA_PASS

Usage: python 05_fetch_viirs.py [--db ../data/svcii.db]
"""
import sys
import os
import requests
from utils import get_conn, log, ensure_data_dir

DB_PATH = sys.argv[sys.argv.index("--db") + 1] if "--db" in sys.argv else "../data/svcii.db"

EARTHDATA_USER = os.getenv("EARTHDATA_USER", "")
EARTHDATA_PASS = os.getenv("EARTHDATA_PASS", "")

# NASA Black Marble annual composite endpoint
LAADS_BASE = "https://ladsweb.modaps.eosdis.nasa.gov/api/v2/content/archives/allData/5000/VNP46A4"


def fetch_ntl_for_point(lat: float, lon: float, year: int, session: requests.Session) -> float | None:
    """
    Fetch annual mean NTL radiance (nW/cm²/sr) for a point.
    Uses the LAADS tile lookup + HDF5 pixel extraction.
    """
    try:
        import h5py
        import numpy as np
    except ImportError:
        log.warning("h5py/numpy not installed. pip install h5py numpy")
        return None

    # Compute VIIRS tile h/v from lat/lon
    h = int((lon + 180) / 10)
    v = int((90 - lat) / 10)

    url = f"{LAADS_BASE}/{year}/001/VNP46A4.A{year}001.h{h:02d}v{v:02d}.001.*.h5"
    try:
        resp = session.get(
            f"https://ladsweb.modaps.eosdis.nasa.gov/api/v2/content/archives/allData/5000/VNP46A4/{year}/001/",
            timeout=30,
        )
        resp.raise_for_status()
        files = [f for f in resp.json() if f.get("name", "").endswith(".h5")
                 and f"h{h:02d}v{v:02d}" in f.get("name", "")]
        if not files:
            return None

        file_url = f"https://ladsweb.modaps.eosdis.nasa.gov{files[0]['downloadsLink']}"
        hdf_resp = session.get(file_url, timeout=120, stream=True)
        hdf_resp.raise_for_status()

        tmp = f"/tmp/vnp46_{h}_{v}_{year}.h5"
        with open(tmp, "wb") as f:
            for chunk in hdf_resp.iter_content(1024 * 1024):
                f.write(chunk)

        with h5py.File(tmp, "r") as hf:
            ntl = hf["HDFEOS/GRIDS/VNP_Grid_DNB/Data Fields/AllAngle_Composite_Snow_Free"][:]
            ntl = ntl.astype(float)
            ntl[ntl == 65535] = np.nan  # fill value

            # Convert lat/lon to pixel
            tile_size = 2400
            px_lat = int((90 - lat - v * 10) / 10 * tile_size)
            px_lon = int((lon + 180 - h * 10) / 10 * tile_size)
            px_lat = max(0, min(px_lat, tile_size - 1))
            px_lon = max(0, min(px_lon, tile_size - 1))

            # 5×5 neighbourhood mean
            region = ntl[max(0, px_lat - 2):px_lat + 3, max(0, px_lon - 2):px_lon + 3]
            return float(np.nanmean(region)) * 0.1  # scale factor

    except Exception as e:
        log.warning(f"VIIRS fetch error: {e}")
        return None


def main():
    conn = get_conn(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, latitude, longitude FROM facilities")
    facilities = cur.fetchall()

    if not facilities:
        log.warning("No facilities found.")
        conn.close()
        return

    if not EARTHDATA_USER:
        log.warning("EARTHDATA_USER not set. Skipping VIIRS download — seeded data will be used.")
        conn.close()
        return

    session = requests.Session()
    session.auth = (EARTHDATA_USER, EARTHDATA_PASS)

    inserted = 0
    for fac_id, lat, lon in facilities:
        for year in [2020, 2021, 2022]:
            val = fetch_ntl_for_point(lat, lon, year, session)
            if val is not None:
                cur.execute(
                    "INSERT OR REPLACE INTO satellite_readings (facility_id, data_type, period_start, period_end, value, unit, source) VALUES (?,?,?,?,?,?,?)",
                    (fac_id, "viirs_ntl", f"{year}-01-01", f"{year}-12-31",
                     round(val, 4), "nW/cm2/sr", "NASA VIIRS Black Marble VNP46A2"),
                )
                inserted += 1

    conn.commit()
    conn.close()
    log.info(f"Inserted {inserted} VIIRS NTL readings.")


if __name__ == "__main__":
    main()
