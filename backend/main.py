import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request

import database as db
import models

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="SVCII API",
    description="Satellite-Verified Corporate Impact Index — greenwashing detection platform",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "https://svcii.vercel.app,http://localhost:3000,http://localhost:3001"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    db.init_db()
    db.seed_if_empty()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/companies", response_model=list[models.CompanyListItem])
@limiter.limit("20/minute")
def list_companies(
    request: Request,
    sector: str | None = Query(None),
    classification: str | None = Query(None),
    metric_type: str | None = Query(None),
    min_score: float | None = Query(None, ge=0, le=100),
    max_score: float | None = Query(None, ge=0, le=100),
):
    rows = db.get_all_companies(sector, classification, metric_type, min_score, max_score)
    return [
        models.CompanyListItem(
            ticker=r["ticker"],
            name=r["name"],
            sector=r["sector"],
            industry=r["industry"],
            market_cap_b=r["market_cap_b"],
            msci_esg_rating=r["msci_esg_rating"],
            svcii=r["svcii"],
            e_score=r["e_score"],
            s_score=r["s_score"],
            classification=r["classification"],
        )
        for r in rows
    ]


@app.get("/api/companies/{ticker}", response_model=models.SVCIIScore)
@limiter.limit("20/minute")
def get_company(request: Request, ticker: str):
    company = db.get_company(ticker)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

    score = db.get_score(ticker)
    if not score:
        raise HTTPException(status_code=404, detail=f"No SVCII score computed for '{ticker}'")

    e_score = models.EScore(
        e_score=score["e_score"] or 0,
        components=models.EScoreComponents(
            trend_direction=score["e_trend_direction"] or 0,
            magnitude=score["e_magnitude_score"] or 0,
            temporal=score["e_temporal_score"] or 0,
            disclosure=score["e_disclosure_score"] or 0,
        ),
        divergence_pct=score["divergence_pct"],
        metric_type=score["metric_type"],
    )

    s_score: models.SScore
    if score["s_score"] is not None:
        s_score = models.SScore(
            s_score=score["s_score"],
            components=models.SScoreComponents(
                land_integrity=score["s_land_integrity"] or 0,
                community_prosperity=score["s_community_prosperity"] or 0,
                supply_chain=score["s_supply_chain"] or 0,
            ),
            weights=models.SScoreWeights(w_land=0.33, w_community=0.33, w_supply=0.34),
        )
    else:
        s_score = models.SScore(reason="No verifiable social claims found")

    return models.SVCIIScore(
        ticker=score["ticker"],
        svcii=score["svcii"],
        e_score=e_score,
        s_score=s_score,
        classification=score["classification"],
        methodology=score["methodology"],
        last_updated=score["last_updated"],
        data_vintage=score["data_vintage"] or "2023–2024",
    )


@app.get("/api/companies/{ticker}/claims", response_model=list[models.ESGClaim])
@limiter.limit("20/minute")
def get_claims(request: Request, ticker: str):
    company = db.get_company(ticker)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

    claims = db.get_claims(ticker)
    score = db.get_score(ticker)
    trend_dir = score["e_trend_direction"] if score else 0

    result = []
    for c in claims:
        # Determine satellite consistency for environmental claims
        sat_consistent: str | None = None
        if c["category"] == "environmental" and c["magnitude_pct"] is not None:
            claimed_dir = -1 if c["magnitude_pct"] < 0 else 1
            if claimed_dir == trend_dir:
                sat_consistent = "consistent"
            elif trend_dir == 0:
                sat_consistent = "inconclusive"
            else:
                sat_consistent = "divergent"

        result.append(
            models.ESGClaim(
                id=c["id"],
                ticker=c["ticker"],
                claim_text=c["claim_text"],
                category=c["category"],
                subcategory=c["subcategory"],
                metric_type=c["metric_type"],
                baseline_year=c["baseline_year"],
                target_year=c["target_year"],
                magnitude_pct=c["magnitude_pct"],
                source_doc=c["source_doc"],
                page_number=c["page_number"],
                satellite_consistent=sat_consistent,
            )
        )
    return result


@app.get("/api/companies/{ticker}/facilities", response_model=list[models.Facility])
@limiter.limit("20/minute")
def get_facilities(request: Request, ticker: str):
    company = db.get_company(ticker)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

    facilities = db.get_facilities(ticker)
    return [
        models.Facility(
            id=f["id"],
            ticker=f["ticker"],
            facility_name=f["facility_name"],
            latitude=f["latitude"],
            longitude=f["longitude"],
            operation_type=f["operation_type"],
            country=f["country"],
            region=f["region"],
            xch4_value=f["xch4_value"],
            xch4_trend=f["xch4_trend"],
            ntl_value=f["ntl_value"],
        )
        for f in facilities
    ]


@app.get("/api/scores/distribution", response_model=list[models.ScoreDistribution])
@limiter.limit("20/minute")
def score_distribution(request: Request):
    return [models.ScoreDistribution(**b) for b in db.get_score_distribution()]


@app.get("/api/scores/by-sector", response_model=list[models.SectorScore])
@limiter.limit("20/minute")
def by_sector(request: Request):
    rows = db.get_sector_scores()
    return [
        models.SectorScore(
            sector=r["sector"],
            avg_svcii=round(r["avg_svcii"], 1),
            avg_e_score=round(r["avg_e_score"], 1),
            avg_s_score=round(r["avg_s_score"], 1) if r["avg_s_score"] else None,
            company_count=r["company_count"],
            consistent_count=r["consistent_count"],
            divergent_count=r["divergent_count"],
        )
        for r in rows
    ]


@app.get("/api/scores/leaderboard", response_model=models.Leaderboard)
@limiter.limit("20/minute")
def leaderboard(request: Request):
    top, bottom = db.get_leaderboard(10)
    return models.Leaderboard(
        top=[models.LeaderboardEntry(**dict(r)) for r in top],
        bottom=[models.LeaderboardEntry(**dict(r)) for r in bottom],
    )


@app.get("/api/search", response_model=list[models.SearchResult])
@limiter.limit("20/minute")
def search(request: Request, q: str = Query(..., min_length=1, max_length=100)):
    rows = db.search_companies(q.strip())
    return [
        models.SearchResult(
            ticker=r["ticker"],
            name=r["name"],
            sector=r["sector"],
            svcii=r["svcii"],
            classification=r["classification"],
        )
        for r in rows
    ]


@app.get("/api/stats", response_model=models.StatsResponse)
@limiter.limit("20/minute")
def stats(request: Request):
    return models.StatsResponse(**db.get_stats())


@app.get("/api/methodology", response_model=models.MethodologyResponse)
@limiter.limit("20/minute")
def methodology(request: Request):
    return models.MethodologyResponse(
        e_score={
            "weight": "60% of SVCII",
            "components": {
                "trend_direction": "40 pts — does satellite XCH4 trend match claimed reduction direction?",
                "magnitude": "30 pts — is satellite-observed change proportional to claimed magnitude?",
                "temporal": "20 pts — is the trend consistent over the full claim period?",
                "disclosure": "10 pts — is the claim absolute (10) or intensity-based (0)?",
            },
            "intensity_penalty": "-10 pts if intensity-based claim",
            "range": "0–100",
        },
        s_score={
            "weight": "40% of SVCII",
            "components": {
                "land_integrity": "ESA WorldCover land cover change detection (0–100)",
                "community_prosperity": "NASA VIIRS Black Marble nighttime lights diff-in-diff (0–100)",
                "supply_chain": "WorldCover land classification around supply chain facilities (0–100)",
            },
            "weighting": "Weighted by number of verifiable claims per category",
            "range": "0–100, or N/A if no verifiable social claims",
        },
        svcii={
            "formula": "0.6 × E-Score + 0.4 × S-Score (E-only if no social claims)",
            "range": "0–100",
        },
        classifications={
            "CONSISTENT": "Score ≥ 80 — satellite data directionally consistent with ESG claims",
            "INCONCLUSIVE": "Score 60–79 — mixed signals, further review recommended",
            "WARRANTS INVESTIGATION": "Score 40–59 — notable divergence between claims and satellite data",
            "MAJOR DIVERGENCE": "Score < 40 — satellite data significantly contradicts ESG claims",
        },
        data_sources=[
            {
                "name": "Sentinel-5P TROPOMI",
                "description": "ESA satellite measuring atmospheric methane (XCH4) at 5.5×3.5 km resolution",
                "url": "https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_CH4",
                "vintage": "2021–2023",
            },
            {
                "name": "EPA GHGRP",
                "description": "EPA Greenhouse Gas Reporting Program — facility-level methane emissions",
                "url": "https://www.epa.gov/ghgreporting/ghg-reporting-program-data-sets",
                "vintage": "2022",
            },
            {
                "name": "NASA VIIRS Black Marble",
                "description": "Nighttime lights from VIIRS DNB — proxy for economic activity and community prosperity",
                "url": "https://ladsweb.modaps.eosdis.nasa.gov/",
                "vintage": "2020–2023",
            },
            {
                "name": "ESA WorldCover",
                "description": "10m global land cover classification — for land integrity and supply chain analysis",
                "url": "https://worldcover2021.esa.int/",
                "vintage": "2020–2021",
            },
            {
                "name": "Global Energy Monitor",
                "description": "Facility coordinates for S&P 500 energy companies",
                "url": "https://www.gem.wiki",
                "vintage": "2023",
            },
        ],
        limitations=[
            "Satellite attribution is correlational, not causal — XCH4 increases near a facility do not prove that facility is the source.",
            "TROPOMI resolution (5.5×3.5 km) may capture emissions from multiple facilities or non-company sources.",
            "ESG claims are extracted from self-reported sustainability reports and may contain ambiguous language.",
            "WorldCover and VIIRS data are best-available proxies, not direct measurements of company impact.",
            "Scores are computed from data vintages 2021–2023; company performance may have changed.",
            "Only companies with publicly available ESG reports and facility coordinates are included.",
        ],
        references=[
            {
                "citation": "Jean, N. et al. (2016). Combining satellite imagery and machine learning to predict poverty. Science, 353(6301), 790–794.",
                "doi": "10.1126/science.aaf7894",
            },
            {
                "citation": "Alvarez, R.A. et al. (2018). Assessment of methane emissions from the U.S. oil and gas supply chain. Science, 361(6398), 186–188.",
                "doi": "10.1126/science.aar7204",
            },
            {
                "citation": "Varon, D.J. et al. (2021). Continuous weekly monitoring of methane emissions from the Permian Basin by inversion of TROPOMI satellite observations. Atmospheric Chemistry and Physics, 21, 7189–7204.",
                "doi": "10.5194/acp-21-7189-2021",
            },
            {
                "citation": "Elvidge, C.D. et al. (2017). VIIRS Night-Time Lights. International Journal of Remote Sensing, 38(21), 5860–5879.",
                "doi": "10.1080/01431161.2017.1342050",
            },
        ],
    )


# ---------------------------------------------------------------------------
# Alias endpoints expected by the frontend / Railway deploy
# ---------------------------------------------------------------------------

@app.get("/api/company/{ticker}", response_model=models.SVCIIScore)
@limiter.limit("20/minute")
def get_company_alias(request: Request, ticker: str):
    return get_company(request, ticker)


@app.get("/api/leaderboard", response_model=models.Leaderboard)
@limiter.limit("20/minute")
def leaderboard_alias(request: Request):
    return leaderboard(request)


@app.get("/api/sectors", response_model=list[models.SectorScore])
@limiter.limit("20/minute")
def sectors_alias(request: Request):
    return by_sector(request)


@app.get("/api/scores", response_model=list[models.ScoreDistribution])
@limiter.limit("20/minute")
def scores_alias(request: Request):
    return score_distribution(request)
