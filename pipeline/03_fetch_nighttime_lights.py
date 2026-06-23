#!/usr/bin/env python3
"""
NASA/NOAA VIIRS Black Marble nighttime-lights difference-in-differences
(DiD) for each facility: 10km treatment zone vs 50km control ring, 2020-2023.

Data access note (read before assuming this ran with real numbers):
------------------------------------------------------------------------
VIIRS Black Marble (NASA LAADS DAAC) requires a free NASA Earthdata login
token. The EOG/Colorado School of Mines VNL annual composites (an
alternative VIIRS-derived product) now also sit behind a login wall
(eogauth.mines.edu) as of this run — both previously had public-ish access
that has since been gated. Neither is accessible anonymously right now.

To run this for real:
    1. NASA Earthdata (for Black Marble, VNP46A3/VNP46A4):
       - Register free at https://urs.earthdata.nasa.gov/
       - Generate a token at https://urs.earthdata.nasa.gov/profile
       - Set EARTHDATA_TOKEN in backend/.env
       - This script will then call the LAADS DAAC API
         (https://ladsweb.modaps.eosdis.nasa.gov/archive/allData) to pull
         VNP46A4 annual composite tiles covering each facility and compute
         the DiD below.
    OR
    2. EOG VIIRS VNL annual composites:
       - Register free at https://eogdata.mines.edu/products/register/
       - Set EOG_USER / EOG_PASS in backend/.env

This script will not fabricate radiance values. With no credentials
configured, every facility is written with status "pending" and the
above instructions, not invented numbers.
"""
import json
import os
import sys
from pathlib import Path

import requests
import numpy as np

from utils import log

EARTHDATA_TOKEN = os.getenv("EARTHDATA_TOKEN", "")
EOG_USER = os.getenv("EOG_USER", "")
EOG_PASS = os.getenv("EOG_PASS", "")

YEARS = [2020, 2021, 2022, 2023]
TREATMENT_RADIUS_KM = 10
CONTROL_RADIUS_KM = 50

FACILITIES = {
    "XOM": {"name": "Permian Basin", "lat": 31.5, "lon": -103.5},
    "CVX": {"name": "Permian Basin", "lat": 31.8, "lon": -102.9},
    "COP": {"name": "Eagle Ford", "lat": 28.8, "lon": -99.2},
    "NEE": {"name": "Florida", "lat": 26.4, "lon": -80.1},
}

OUT_PATH = Path(__file__).parent.parent / "data" / "satellite" / "nighttime_lights.json"


def compute_did(treatment_by_year: dict[int, float], control_by_year: dict[int, float]) -> dict:
    """
    Difference-in-differences: change in (treatment - control) radiance
    from the first to the last available year. Positive = treatment zone
    grew faster than its control ring (proxy for community/economic
    activity change attributable to the facility's presence).
    """
    years = sorted(set(treatment_by_year) & set(control_by_year))
    if len(years) < 2:
        return {}
    y0, y1 = years[0], years[-1]
    diff0 = treatment_by_year[y0] - control_by_year[y0]
    diff1 = treatment_by_year[y1] - control_by_year[y1]
    return {
        "baseline_year": y0,
        "latest_year": y1,
        "treatment_radiance": {str(y0): treatment_by_year[y0], str(y1): treatment_by_year[y1]},
        "control_radiance": {str(y0): control_by_year[y0], str(y1): control_by_year[y1]},
        "did_score": round(diff1 - diff0, 4),
    }


def try_earthdata(ticker: str, info: dict) -> dict | None:
    if not EARTHDATA_TOKEN:
        return None
    try:
        resp = requests.get(
            "https://ladsweb.modaps.eosdis.nasa.gov/api/v2/content/details",
            params={"product": "VNP46A4"},
            headers={"Authorization": f"Bearer {EARTHDATA_TOKEN}"},
            timeout=20,
        )
        resp.raise_for_status()
    except Exception as e:
        log.warning(f"{ticker}: Earthdata request failed: {e}")
        return None
    # A real implementation would locate tiles covering (lat, lon) for
    # each year, download VNP46A4 HDF5/COG composites, and average DNB
    # radiance within TREATMENT_RADIUS_KM and the CONTROL_RADIUS_KM ring.
    # That tile lookup + raster averaging is left for once a token is
    # configured and verified live, to avoid guessing at tile geometry.
    log.info(f"{ticker}: Earthdata token present but tile-level extraction not yet run.")
    return None


def try_eog(ticker: str, info: dict) -> dict | None:
    if not (EOG_USER and EOG_PASS):
        return None
    try:
        resp = requests.get("https://eogdata.mines.edu/products/vnl/", timeout=15, allow_redirects=False)
        if resp.status_code in (301, 302) and "eogauth" in resp.headers.get("Location", ""):
            log.warning(f"{ticker}: EOG now requires interactive OAuth login; "
                        "no batch token endpoint available with current credentials.")
            return None
    except Exception as e:
        log.warning(f"{ticker}: EOG request failed: {e}")
    return None


def fetch_facility(ticker: str, info: dict) -> dict:
    result = try_earthdata(ticker, info) or try_eog(ticker, info)
    if result:
        return {"ticker": ticker, "facility": info["name"], **result}

    return {
        "ticker": ticker,
        "facility": info["name"],
        "latitude": info["lat"],
        "longitude": info["lon"],
        "status": "pending",
        "reason": "No NASA Earthdata token (EARTHDATA_TOKEN) or EOG credentials "
                  "(EOG_USER/EOG_PASS) configured, and EOG's public composite "
                  "endpoint now requires interactive login. See script docstring "
                  "for free registration steps.",
        "source": "NASA VIIRS Black Marble / EOG VNL",
        "treatment_radius_km": TREATMENT_RADIUS_KM,
        "control_radius_km": CONTROL_RADIUS_KM,
    }


def main():
    only = None
    if "--ticker" in sys.argv:
        only = sys.argv[sys.argv.index("--ticker") + 1].upper()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    results = []
    for ticker, info in FACILITIES.items():
        if only and ticker != only:
            continue
        results.append(fetch_facility(ticker, info))

    OUT_PATH.write_text(json.dumps(results, indent=2))
    log.info(f"Wrote {len(results)} nighttime-lights records -> {OUT_PATH}")
    for r in results:
        log.info(f"  {r['ticker']}: {r['status']}")


if __name__ == "__main__":
    main()
