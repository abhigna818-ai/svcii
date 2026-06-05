"""
SVCII scoring functions.
These operate on pre-computed satellite data stored in the DB.
"""
from datetime import datetime
import math


def classify_score(score: float) -> str:
    if score >= 80:
        return "CONSISTENT"
    if score >= 60:
        return "INCONCLUSIVE"
    if score >= 40:
        return "WARRANTS INVESTIGATION"
    return "MAJOR DIVERGENCE"


def compute_temporal_consistency(readings: list[dict]) -> float:
    """
    Given a list of {period_end, value} dicts sorted by period,
    compute a temporal consistency score 0-20.
    Checks if the trend is monotonic or noisy.
    """
    if len(readings) < 3:
        return 10.0  # insufficient data → neutral

    values = [r["value"] for r in readings]
    n = len(values)
    direction_changes = 0
    for i in range(1, n - 1):
        d1 = values[i] - values[i - 1]
        d2 = values[i + 1] - values[i]
        if d1 * d2 < 0:
            direction_changes += 1

    max_changes = n - 2
    consistency_ratio = 1.0 - (direction_changes / max_changes) if max_changes > 0 else 1.0
    return round(consistency_ratio * 20, 1)


def compute_e_score(
    claimed_magnitude_pct: float,
    metric_type: str,
    satellite_pct_change: float,
    satellite_trend_direction: int,
    temporal_readings: list[dict],
) -> dict:
    """
    E Score (0-100): compare company methane claims vs satellite-observed trends.

    Args:
        claimed_magnitude_pct: negative = reduction (e.g. -20 means 20% reduction claimed)
        metric_type: 'absolute', 'intensity', or 'ambiguous'
        satellite_pct_change: actual % change observed via satellite (negative = decrease)
        satellite_trend_direction: -1 (decreasing), 0 (stable), 1 (increasing)
        temporal_readings: list of {period_end, value} for temporal consistency
    """
    # Component 1: Trend Direction Agreement (40 pts)
    claimed_direction = -1 if claimed_magnitude_pct < 0 else 1
    if claimed_direction == satellite_trend_direction:
        trend_score = 40.0
    elif satellite_trend_direction == 0:
        trend_score = 20.0
    else:
        trend_score = 0.0

    # Component 2: Magnitude Proportionality (30 pts)
    divergence = abs(claimed_magnitude_pct - satellite_pct_change)
    magnitude_score = max(0.0, 30.0 - (divergence * 0.6))

    # Component 3: Temporal Consistency (20 pts)
    consistency_score = compute_temporal_consistency(temporal_readings)

    # Component 4: Disclosure Quality (10 pts)
    disclosure_score = 10.0 if metric_type == "absolute" else 0.0

    raw_score = trend_score + magnitude_score + consistency_score + disclosure_score

    # Intensity penalty
    if metric_type == "intensity":
        raw_score = max(0.0, raw_score - 10.0)

    e_score = round(min(100.0, max(0.0, raw_score)), 1)

    return {
        "e_score": e_score,
        "components": {
            "trend_direction": trend_score,
            "magnitude": round(magnitude_score, 1),
            "temporal": round(consistency_score, 1),
            "disclosure": disclosure_score,
        },
        "divergence_pct": round(divergence, 2),
        "metric_type": metric_type,
        "satellite_source": "Sentinel-5P TROPOMI / NOAA CarbonTracker",
    }


def compute_s_score(
    land_integrity: float | None,
    community_prosperity: float | None,
    supply_chain: float | None,
    land_claims: int,
    community_claims: int,
    supply_claims: int,
) -> dict:
    """
    S Score (0-100): weighted by claim count per category.
    """
    total_claims = land_claims + community_claims + supply_claims
    if total_claims == 0:
        return {
            "s_score": None,
            "reason": "No verifiable social claims found",
            "satellite_sources": ["ESA WorldCover 2020/2021", "NASA VIIRS Black Marble"],
        }

    # Default sub-scores to 50 (neutral) if no satellite data
    lis = land_integrity if land_integrity is not None else 50.0
    cps = community_prosperity if community_prosperity is not None else 50.0
    slus = supply_chain if supply_chain is not None else 50.0

    w1 = land_claims / total_claims
    w2 = community_claims / total_claims
    w3 = supply_claims / total_claims

    s_score = (w1 * lis) + (w2 * cps) + (w3 * slus)

    return {
        "s_score": round(s_score, 1),
        "components": {
            "land_integrity": round(lis, 1),
            "community_prosperity": round(cps, 1),
            "supply_chain": round(slus, 1),
        },
        "weights": {"w_land": round(w1, 3), "w_community": round(w2, 3), "w_supply": round(w3, 3)},
        "satellite_sources": ["ESA WorldCover 2020/2021", "NASA VIIRS Black Marble"],
    }


def compute_svcii(e_result: dict, s_result: dict, ticker: str) -> dict:
    e_val = e_result["e_score"]
    s_val = s_result.get("s_score")

    if s_val is None:
        svcii = e_val
        methodology = "E-only (no verifiable social claims)"
    else:
        svcii = round((0.6 * e_val) + (0.4 * s_val), 1)
        methodology = "60% Environmental / 40% Social"

    classification = classify_score(svcii)

    return {
        "ticker": ticker,
        "svcii": round(svcii, 1),
        "e_score": e_result,
        "s_score": s_result,
        "classification": classification,
        "methodology": methodology,
        "last_updated": datetime.utcnow().isoformat(),
        "data_vintage": "2023–2024",
    }
