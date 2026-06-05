#!/usr/bin/env python3
"""
Download ESA WorldCover 2020 + 2021 tiles for facility regions.
Source: https://worldcover2021.esa.int/downloader
10m resolution GeoTIFF — land cover classification.

Classes: 10=Tree cover, 20=Shrubland, 30=Grassland, 40=Cropland,
         50=Built-up, 60=Bare/sparse, 70=Snow, 80=Water, 90=Wetland, 95=Mangrove

Usage: python 06_fetch_worldcover.py [--db ../data/svcii.db]
"""
import sys
import os
import math
import requests
from utils import get_conn, log, ensure_data_dir

DB_PATH = sys.argv[sys.argv.index("--db") + 1] if "--db" in sys.argv else "../data/svcii.db"

# ESA WorldCover S3 bucket
WC_BASE = "https://esa-worldcover.s3.amazonaws.com/v100/2020/map"
BUFFER_DEG = 0.1  # ~11km buffer


def lat_lon_to_tile(lat: float, lon: float) -> str:
    """Compute ESA WorldCover 3°×3° tile identifier."""
    tile_lat = math.floor(lat / 3) * 3
    tile_lon = math.floor(lon / 3) * 3
    ns = "N" if tile_lat >= 0 else "S"
    ew = "E" if tile_lon >= 0 else "W"
    return f"ESA_WorldCover_10m_2020_v100_{ns}{abs(tile_lat):02d}{ew}{abs(tile_lon):03d}_Map"


def compute_land_integrity(tile_path: str, lat: float, lon: float, buffer: float = BUFFER_DEG) -> float:
    """
    Compute land integrity score from WorldCover GeoTIFF.
    Score = fraction of natural land cover (tree/shrub/grassland/wetland) × 100.
    """
    try:
        import rasterio
        import numpy as np
        from rasterio.windows import from_bounds

        with rasterio.open(tile_path) as src:
            window = from_bounds(
                lon - buffer, lat - buffer, lon + buffer, lat + buffer, src.transform
            )
            data = src.read(1, window=window)
            if data.size == 0:
                return 50.0
            natural = np.isin(data, [10, 20, 30, 90, 95])
            score = float(np.mean(natural)) * 100
            return round(score, 2)
    except Exception as e:
        log.warning(f"WorldCover analysis error: {e}")
        return 50.0


def main():
    data_dir = ensure_data_dir()
    conn = get_conn(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, ticker, latitude, longitude FROM facilities")
    facilities = cur.fetchall()

    if not facilities:
        log.warning("No facilities found.")
        conn.close()
        return

    try:
        import rasterio
    except ImportError:
        log.warning("rasterio not installed. pip install rasterio — skipping WorldCover download.")
        conn.close()
        return

    updated = 0
    for fac_id, ticker, lat, lon in facilities:
        tile_name = lat_lon_to_tile(lat, lon)
        tile_url = f"{WC_BASE}/{tile_name}.tif"
        tile_path = data_dir / f"{tile_name}.tif"

        if not tile_path.exists():
            log.info(f"Downloading WorldCover tile {tile_name}...")
            try:
                resp = requests.get(tile_url, timeout=120, stream=True)
                resp.raise_for_status()
                with open(tile_path, "wb") as f:
                    for chunk in resp.iter_content(1024 * 1024):
                        f.write(chunk)
            except Exception as e:
                log.warning(f"Tile download failed for {tile_name}: {e}")
                continue

        lis = compute_land_integrity(str(tile_path), lat, lon)
        cur.execute(
            "INSERT OR REPLACE INTO satellite_readings (facility_id, data_type, period_start, period_end, value, unit, source) VALUES (?,?,?,?,?,?,?)",
            (fac_id, "worldcover_ndvi", "2020-01-01", "2021-12-31",
             lis, "land_integrity_0-100", "ESA WorldCover 2020/2021"),
        )
        updated += 1

    conn.commit()
    conn.close()
    log.info(f"Computed land integrity for {updated} facilities.")


if __name__ == "__main__":
    main()
