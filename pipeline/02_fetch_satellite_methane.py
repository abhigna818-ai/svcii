#!/usr/bin/env python3
"""
Fetch real, satellite-informed methane data for each company's primary
facility region and compute YoY % change in methane emissions, 2020-2023.

Data source note (read before relying on this for "raw TROPOMI XCH4"):
------------------------------------------------------------------------
Direct Sentinel-5P TROPOMI XCH4 column-concentration access requires an
authenticated account (Copernicus Data Space Ecosystem, free to register
at https://dataspace.copernicus.eu/, or Google Earth Engine via
`earthengine authenticate`). Since no credentials are configured for this
project, this script instead uses Climate TRACE
(https://climatetrace.org/data, https://api.climatetrace.org), a free,
public, no-authentication API that publishes asset-level methane (CH4)
emissions estimates derived in part from satellite remote sensing and
peer-reviewed inventory methods. It is a legitimate independent,
satellite-informed cross-check — just not raw column-concentration data.

To switch to raw TROPOMI XCH4 once you have credentials:
    1. Register at https://dataspace.copernicus.eu/ (free)
    2. Set COPERNICUS_USER / COPERNICUS_PASS in backend/.env
    3. Re-implement fetch_region() to pull L2__CH4___ granules via the
       Copernicus Data Space STAC API and average pixels in each facility
       buffer with xarray/harp, instead of calling Climate TRACE.

No values in this script are fabricated. If Climate TRACE returns no
matching assets for a facility (e.g. NextEra, a utility with no oil & gas
production footprint), the reading is marked "pending" rather than guessed.
"""
import json
import math
import sys
from pathlib import Path

import requests

from utils import log

API_BASE = "https://api.climatetrace.org/v6"
YEARS = [2020, 2021, 2022, 2023]
BUFFER_KM = 80  # radius around facility centroid to aggregate matching assets

FACILITIES = {
    "XOM": {"name": "Permian Basin", "lat": 31.5, "lon": -103.5, "sector": "oil-and-gas-production"},
    "CVX": {"name": "Permian Basin", "lat": 31.8, "lon": -102.9, "sector": "oil-and-gas-production"},
    "COP": {"name": "Eagle Ford", "lat": 28.8, "lon": -99.2, "sector": "oil-and-gas-production"},
    "NEE": {"name": "Florida", "lat": 26.4, "lon": -80.1, "sector": "oil-and-gas-production"},
}

OUT_PATH = Path(__file__).parent.parent / "data" / "satellite" / "methane_readings.json"


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def list_assets(sector: str, country: str = "USA", max_assets: int = 3000) -> list[dict]:
    assets = []
    limit = 1000
    offset = 0
    while len(assets) < max_assets:
        try:
            resp = requests.get(
                f"{API_BASE}/assets",
                params={"countries": country, "sector": sector, "limit": limit, "offset": offset},
                timeout=30,
            )
            resp.raise_for_status()
            batch = resp.json().get("assets", [])
        except Exception as e:
            log.warning(f"Climate TRACE asset list failed at offset={offset}: {e}")
            break
        if not batch:
            break
        assets.extend(batch)
        if len(batch) < limit:
            break
        offset += limit
    return assets


def assets_near(assets: list[dict], lat: float, lon: float, radius_km: float) -> list[dict]:
    nearby = []
    for a in assets:
        centroid = a.get("Centroid", {}).get("Geometry")
        if not centroid or len(centroid) != 2:
            continue
        a_lon, a_lat = centroid
        if haversine_km(lat, lon, a_lat, a_lon) <= radius_km:
            nearby.append(a)
    return nearby


def ch4_by_year(asset_id: int) -> dict[int, float]:
    try:
        resp = requests.get(f"{API_BASE}/assets/{asset_id}", timeout=30)
        resp.raise_for_status()
        details = resp.json().get("EmissionsDetails", [])
    except Exception as e:
        log.warning(f"Asset {asset_id} detail fetch failed: {e}")
        return {}
    out = {}
    for d in details:
        if d.get("Gas") == "ch4" and d.get("EmissionsQuantity") is not None:
            out[d["Year"]] = out.get(d["Year"], 0.0) + d["EmissionsQuantity"]
    return out


def fetch_region(ticker: str, info: dict) -> dict:
    log.info(f"{ticker}: searching Climate TRACE assets near {info['name']} "
             f"({info['lat']}, {info['lon']})...")
    assets = list_assets(info["sector"])
    nearby = assets_near(assets, info["lat"], info["lon"], BUFFER_KM)
    log.info(f"{ticker}: {len(nearby)} assets within {BUFFER_KM}km of {info['name']}")

    if not nearby:
        return {
            "ticker": ticker,
            "facility": info["name"],
            "latitude": info["lat"],
            "longitude": info["lon"],
            "status": "pending",
            "reason": "No matching Climate TRACE oil & gas assets within radius. "
                      "Raw TROPOMI XCH4 requires Copernicus Data Space credentials "
                      "(see script docstring).",
            "source": "Climate TRACE",
        }

    totals: dict[int, float] = {}
    matched = 0
    for asset in nearby:
        yearly = ch4_by_year(asset["Id"])
        if not yearly:
            continue
        matched += 1
        for y, v in yearly.items():
            totals[y] = totals.get(y, 0.0) + v

    if matched == 0 or not totals or all(v == 0 for v in totals.values()):
        return {
            "ticker": ticker,
            "facility": info["name"],
            "latitude": info["lat"],
            "longitude": info["lon"],
            "status": "pending",
            "reason": "Matching assets found but none had usable CH4 emissions detail.",
            "source": "Climate TRACE",
        }

    years_sorted = sorted(totals)

    if len(years_sorted) < 2:
        # The Climate TRACE v6 /assets/{id} endpoint only returns the most
        # recent reporting year per asset — it does not expose a 2020-2023
        # historical series. We report the single real data point we have
        # rather than fabricate a trend. For a true 2020-2023 YoY series,
        # download the Climate TRACE bulk CSVs (monthly source-level data,
        # 2021-2024) at https://climatetrace.org/data, or use Copernicus
        # Data Space TROPOMI access per the script docstring.
        return {
            "ticker": ticker,
            "facility": info["name"],
            "latitude": info["lat"],
            "longitude": info["lon"],
            "status": "partial",
            "reason": "Climate TRACE API exposed only one reporting year "
                      f"({years_sorted[0]}) per asset via this endpoint — no "
                      "2020-2023 trend could be computed without the bulk "
                      "CSV download. See script docstring.",
            "source": "Climate TRACE (climatetrace.org)",
            "matched_assets": matched,
            "ch4_tonnes_by_year": {str(y): round(v, 1) for y, v in totals.items()},
        }

    yoy = {}
    for i in range(1, len(years_sorted)):
        y0, y1 = years_sorted[i - 1], years_sorted[i]
        if totals[y0] > 0:
            yoy[f"{y0}-{y1}"] = round((totals[y1] - totals[y0]) / totals[y0] * 100, 2)

    total_pct_change = None
    if totals[years_sorted[0]] > 0:
        total_pct_change = round(
            (totals[years_sorted[-1]] - totals[years_sorted[0]]) / totals[years_sorted[0]] * 100, 2
        )

    return {
        "ticker": ticker,
        "facility": info["name"],
        "latitude": info["lat"],
        "longitude": info["lon"],
        "status": "ok",
        "source": "Climate TRACE (climatetrace.org) — satellite-informed asset-level CH4 estimates",
        "matched_assets": matched,
        "ch4_tonnes_by_year": {str(y): round(v, 1) for y, v in totals.items()},
        "yoy_pct_change": yoy,
        "pct_change_total": total_pct_change,
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
        results.append(fetch_region(ticker, info))

    OUT_PATH.write_text(json.dumps(results, indent=2))
    log.info(f"Wrote {len(results)} facility methane records -> {OUT_PATH}")
    for r in results:
        status_note = r["status"] if r["status"] == "ok" else f"{r['status']} ({r['reason']})"
        log.info(f"  {r['ticker']}: {status_note}")


if __name__ == "__main__":
    main()
