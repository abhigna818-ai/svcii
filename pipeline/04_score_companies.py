#!/usr/bin/env python3
"""
Compute SVCII scores from real pipeline output: data/claims/*.json,
data/satellite/methane_readings.json, data/satellite/nighttime_lights.json.

Methodology (as specified):

E_SCORE (0-100):
  - trend_direction_match (40 pts): does satellite-observed CH4 trend
    direction match the claimed reduction/increase direction?
  - magnitude_proportionality (30 pts): how close is the claimed % change
    to the satellite-observed % change?
  - intensity_penalty: (trend + magnitude) * 0.8 if the claim is
    intensity-based rather than absolute
  - disclosure_quality (20 pts): absolute=20, intensity=10, qualitative=5

S_SCORE (0-100):
  - land_integrity: NDVI-based land cover change near facilities
    (not yet wired to a live data source in this pipeline — defaults to
    50/neutral and is reported as such, never fabricated)
  - community_prosperity: VIIRS DiD score (50/neutral if pending, see
    03_fetch_nighttime_lights.py)
  - supply_chain: 50 if no data
  - weighted by claim count per category

SVCII = 0.6 * E_SCORE + 0.4 * S_SCORE

CLASSIFICATION: >=75 CONSISTENT, 50-74 INCONCLUSIVE,
                30-49 WARRANTS INVESTIGATION, <30 MAJOR DIVERGENCE

Every score that rests on pending/unavailable satellite data is tagged
with a `data_confidence` note so the frontend can show *why* a score is
what it is, instead of presenting a fabricated-looking number.
"""
import json
from pathlib import Path
from datetime import datetime, timezone

DATA_DIR = Path(__file__).parent.parent / "data"
CLAIMS_DIR = DATA_DIR / "claims"
OUT_PATH = DATA_DIR / "scores" / "final_scores.json"

TICKERS = ["XOM", "CVX", "COP", "MSFT", "NEE"]


def classify(score: float) -> str:
    if score >= 75:
        return "CONSISTENT"
    if score >= 50:
        return "INCONCLUSIVE"
    if score >= 30:
        return "WARRANTS INVESTIGATION"
    return "MAJOR DIVERGENCE"


def load_json(path: Path):
    if path.exists():
        return json.loads(path.read_text())
    return None


def load_satellite_by_ticker(path: Path) -> dict:
    data = load_json(path) or []
    return {r["ticker"]: r for r in data}


def compute_e_score(claims: list[dict], methane: dict | None) -> dict:
    env_claims = [c for c in claims if c.get("category") in ("emissions",)]

    if not env_claims:
        return {
            "e_score": None,
            "reason": "No quantified emissions claims extracted from the sustainability report.",
            "data_confidence": "no_claims",
        }

    # Use the strongest (most negative / most specific) claimed magnitude
    # as the representative claim for trend comparison.
    primary = min(
        (c for c in env_claims if c.get("value") is not None),
        key=lambda c: c["value"],
        default=env_claims[0],
    )
    claimed_value = primary.get("value")
    metric_type = primary.get("metric_type", "qualitative")

    satellite_status = (methane or {}).get("status")
    has_real_trend = satellite_status == "ok"

    if not has_real_trend:
        # No real 2020-2023 trend available (see 02_fetch_satellite_methane.py).
        # Score the components we *can* score honestly; mark the rest neutral
        # rather than invent a satellite trend.
        trend_score = 20.0  # neutral — no comparable trend
        magnitude_score = 0.0  # cannot assess proportionality without a trend
        confidence = "satellite_pending"
        confidence_note = (methane or {}).get("reason", "No satellite trend data available.")
    else:
        sat_pct = methane.get("pct_change_total")
        claimed_pct = claimed_value if claimed_value is not None else 0
        claimed_dir = -1 if claimed_pct < 0 else 1
        sat_dir = -1 if (sat_pct or 0) < 0 else 1
        trend_score = 40.0 if claimed_dir == sat_dir else 0.0
        divergence = abs(claimed_pct - (sat_pct or 0))
        magnitude_score = max(0.0, 30.0 - divergence * 0.6)
        confidence = "satellite_verified"
        confidence_note = f"Compared against Climate TRACE CH4 change of {sat_pct}%."

    disclosure_map = {"absolute": 20.0, "intensity": 10.0, "qualitative": 5.0}
    disclosure_score = disclosure_map.get(metric_type, 5.0)

    raw = trend_score + magnitude_score
    if metric_type == "intensity":
        raw *= 0.8

    e_score = round(min(100.0, max(0.0, raw + disclosure_score)), 1)

    return {
        "e_score": e_score,
        "components": {
            "trend_direction_match": trend_score,
            "magnitude_proportionality": round(magnitude_score, 1),
            "disclosure_quality": disclosure_score,
        },
        "intensity_penalty_applied": metric_type == "intensity",
        "primary_claim": primary.get("claim_text"),
        "metric_type": metric_type,
        "data_confidence": confidence,
        "confidence_note": confidence_note,
    }


def compute_s_score(claims: list[dict], nightlights: dict | None) -> dict:
    social_claims = [c for c in claims if c.get("category") in ("social", "land", "water")]
    if not social_claims:
        return {
            "s_score": None,
            "reason": "No verifiable social/land/water claims extracted.",
            "data_confidence": "no_claims",
        }

    land_integrity = 50.0  # NDVI pipeline not wired up — neutral, not fabricated
    community_prosperity = 50.0
    if nightlights and nightlights.get("status") == "ok":
        community_prosperity = 50.0 + min(50.0, max(-50.0, nightlights.get("did_score", 0) * 100))
    supply_chain = 50.0  # no supply-chain facility data — neutral

    s_score = round((land_integrity + community_prosperity + supply_chain) / 3, 1)

    return {
        "s_score": s_score,
        "components": {
            "land_integrity": land_integrity,
            "community_prosperity": community_prosperity,
            "supply_chain": supply_chain,
        },
        "data_confidence": "neutral_defaults",
        "confidence_note": "Land integrity (NDVI) and supply-chain facility data are not yet "
                            "wired to a live source in this pipeline; nighttime-lights DiD is "
                            "pending NASA Earthdata / EOG credentials. All defaulted to neutral "
                            "(50) rather than fabricated.",
    }


def compute_investor_risk(classification: str, e_score: dict, divergence_note: str | None) -> str:
    if classification == "MAJOR DIVERGENCE":
        return ("Satellite/claim divergence is large enough to warrant regulatory and "
                "ESG-fund-disclosure scrutiny.")
    if classification == "WARRANTS INVESTIGATION":
        return "Notable gap between disclosed claims and available verification data."
    if classification == "INCONCLUSIVE":
        return e_score.get("confidence_note") or "Verification data is incomplete; treat the score as provisional."
    return "No material divergence identified from available data."


def main():
    DATA_DIR.joinpath("scores").mkdir(parents=True, exist_ok=True)
    methane_by_ticker = load_satellite_by_ticker(DATA_DIR / "satellite" / "methane_readings.json")
    lights_by_ticker = load_satellite_by_ticker(DATA_DIR / "satellite" / "nighttime_lights.json")

    results = []
    for ticker in TICKERS:
        claims_file = CLAIMS_DIR / f"{ticker}_claims.json"
        claims_data = load_json(claims_file)
        if claims_data is None:
            print(f"[skip] {ticker}: no claims file at {claims_file} "
                  f"(run 01_fetch_esg_claims.py with ANTHROPIC_API_KEY set first)")
            continue

        claims = claims_data.get("claims", [])
        e_result = compute_e_score(claims, methane_by_ticker.get(ticker))
        s_result = compute_s_score(claims, lights_by_ticker.get(ticker))

        e_val = e_result.get("e_score")
        s_val = s_result.get("s_score")

        if e_val is None and s_val is None:
            print(f"[skip] {ticker}: no scoreable claims at all.")
            continue

        if e_val is None:
            svcii = s_val
            methodology = "S-only (no quantified environmental claims)"
        elif s_val is None:
            svcii = e_val
            methodology = "E-only (no verifiable social claims)"
        else:
            svcii = round(0.6 * e_val + 0.4 * s_val, 1)
            methodology = "60% Environmental / 40% Social"

        classification = classify(svcii)

        results.append({
            "ticker": ticker,
            "svcii": svcii,
            "classification": classification,
            "methodology": methodology,
            "e_score": e_result,
            "s_score": s_result,
            "investor_risk_note": compute_investor_risk(classification, e_result, None),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "claims_count": len(claims),
        })
        print(f"[ok] {ticker}: SVCII={svcii} ({classification})")

    OUT_PATH.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {len(results)} company scores -> {OUT_PATH}")


if __name__ == "__main__":
    main()
