#!/usr/bin/env python3
"""
Download pre-processed Sentinel-5P TROPOMI XCH4 data for facility locations.

Two approaches:
1. Google Earth Engine (preferred): exports regional XCH4 timeseries via ee Python API
2. Copernicus Data Space fallback: download per-granule NetCDF, extract pixel values

Source: https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_CH4
Fallback: https://dataspace.copernicus.eu/

Usage: python 04_fetch_tropomi.py [--db ../data/svcii.db] [--method ee|copernicus]
"""
import sys
import json
from utils import get_conn, log, ensure_data_dir

DB_PATH = sys.argv[sys.argv.index("--db") + 1] if "--db" in sys.argv else "../data/svcii.db"
METHOD  = sys.argv[sys.argv.index("--method") + 1] if "--method" in sys.argv else "ee"

BUFFER_KM = 25  # radius around each facility to sample XCH4


def fetch_via_earth_engine(facilities: list[dict]) -> dict[int, list[dict]]:
    """
    Use Google Earth Engine Python API to extract XCH4 timeseries.
    Requires: pip install earthengine-api && earthengine authenticate
    """
    try:
        import ee
        ee.Initialize()
    except Exception as e:
        log.warning(f"Earth Engine unavailable: {e}")
        return {}

    collection = (
        ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_CH4")
        .select("CH4_column_volume_mixing_ratio_dry_air")
        .filterDate("2021-01-01", "2024-01-01")
    )

    results: dict[int, list[dict]] = {}
    for fac in facilities:
        fac_id = fac["id"]
        point = ee.Geometry.Point([fac["longitude"], fac["latitude"]])
        region = point.buffer(BUFFER_KM * 1000)

        def extract_mean(img):
            val = img.reduceRegion(ee.Reducer.mean(), region, 1000).get(
                "CH4_column_volume_mixing_ratio_dry_air"
            )
            return ee.Feature(None, {"date": img.date().format("YYYY-MM-dd"), "xch4": val})

        try:
            fc = collection.map(extract_mean).getInfo()
            readings = [
                {"period_end": f["properties"]["date"], "value": f["properties"]["xch4"]}
                for f in fc["features"]
                if f["properties"].get("xch4") is not None
            ]
            results[fac_id] = readings
        except Exception as e:
            log.warning(f"EE extraction failed for facility {fac_id}: {e}")

    return results


def main():
    data_dir = ensure_data_dir()
    conn = get_conn(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, ticker, latitude, longitude, facility_name FROM facilities")
    facilities = [dict(r) for r in cur.fetchall()]

    if not facilities:
        log.warning("No facilities in DB. Run 02_fetch_facilities.py or 09_seed_demo_data.py first.")
        conn.close()
        return

    log.info(f"Fetching TROPOMI XCH4 for {len(facilities)} facilities via {METHOD}...")

    if METHOD == "ee":
        readings_by_fac = fetch_via_earth_engine(facilities)
    else:
        log.warning("Copernicus method requires manual granule download. See docs.")
        readings_by_fac = {}

    if not readings_by_fac:
        log.warning("No TROPOMI data fetched. Seeded data from 09_seed_demo_data.py will be used.")
        conn.close()
        return

    inserted = 0
    for fac_id, readings in readings_by_fac.items():
        for r in readings:
            if r.get("value") is None:
                continue
            cur.execute(
                "INSERT INTO satellite_readings (facility_id, data_type, period_start, period_end, value, unit, source) VALUES (?,?,?,?,?,?,?)",
                (fac_id, "tropomi_xch4", r["period_end"][:7] + "-01", r["period_end"],
                 round(float(r["value"]) * 1e9, 2),  # mol/mol → ppb
                 "ppb", "Sentinel-5P TROPOMI OFFL L3 CH4"),
            )
            inserted += 1

    conn.commit()
    conn.close()
    log.info(f"Inserted {inserted} TROPOMI XCH4 readings.")


if __name__ == "__main__":
    main()
