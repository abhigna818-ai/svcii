from pydantic import BaseModel
from typing import Optional


class CompanyBase(BaseModel):
    ticker: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap_b: Optional[float] = None
    msci_esg_rating: Optional[str] = None
    sp500: int = 1
    has_esg_report: int = 0
    esg_report_year: Optional[int] = None
    facility_count: Optional[int] = None


class EScoreComponents(BaseModel):
    trend_direction: float
    magnitude: float
    temporal: float
    disclosure: float


class EScore(BaseModel):
    e_score: float
    components: EScoreComponents
    divergence_pct: Optional[float] = None
    metric_type: Optional[str] = None
    satellite_source: str = "Sentinel-5P TROPOMI / NOAA CarbonTracker"


class SScoreComponents(BaseModel):
    land_integrity: float
    community_prosperity: float
    supply_chain: float


class SScoreWeights(BaseModel):
    w_land: float
    w_community: float
    w_supply: float


class SScore(BaseModel):
    s_score: Optional[float] = None
    components: Optional[SScoreComponents] = None
    weights: Optional[SScoreWeights] = None
    satellite_sources: list[str] = ["ESA WorldCover 2020/2021", "NASA VIIRS Black Marble"]
    reason: Optional[str] = None


class SVCIIScore(BaseModel):
    ticker: str
    svcii: Optional[float] = None
    e_score: Optional[EScore] = None
    s_score: Optional[SScore] = None
    classification: Optional[str] = None
    methodology: Optional[str] = None
    last_updated: Optional[str] = None
    data_vintage: str = "2023–2024"


class CompanyListItem(BaseModel):
    ticker: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap_b: Optional[float] = None
    msci_esg_rating: Optional[str] = None
    svcii: Optional[float] = None
    e_score: Optional[float] = None
    s_score: Optional[float] = None
    classification: Optional[str] = None


class ESGClaim(BaseModel):
    id: int
    ticker: str
    claim_text: str
    category: Optional[str] = None
    subcategory: Optional[str] = None
    metric_type: Optional[str] = None
    baseline_year: Optional[int] = None
    target_year: Optional[int] = None
    magnitude_pct: Optional[float] = None
    source_doc: Optional[str] = None
    page_number: Optional[int] = None
    satellite_consistent: Optional[str] = None  # consistent, divergent, inconclusive


class Facility(BaseModel):
    id: int
    ticker: str
    facility_name: str
    latitude: float
    longitude: float
    operation_type: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    xch4_value: Optional[float] = None
    xch4_trend: Optional[float] = None
    ntl_value: Optional[float] = None


class ScoreDistribution(BaseModel):
    bucket_start: float
    bucket_end: float
    count: int
    label: str


class SectorScore(BaseModel):
    sector: str
    avg_svcii: float
    avg_e_score: float
    avg_s_score: Optional[float] = None
    company_count: int
    consistent_count: int
    divergent_count: int


class LeaderboardEntry(BaseModel):
    ticker: str
    name: str
    sector: Optional[str] = None
    svcii: float
    classification: str


class Leaderboard(BaseModel):
    top: list[LeaderboardEntry]
    bottom: list[LeaderboardEntry]


class MethodologyResponse(BaseModel):
    e_score: dict
    s_score: dict
    svcii: dict
    classifications: dict
    data_sources: list[dict]
    limitations: list[str]
    references: list[dict]


class SearchResult(BaseModel):
    ticker: str
    name: str
    sector: Optional[str] = None
    svcii: Optional[float] = None
    classification: Optional[str] = None


class StatsResponse(BaseModel):
    total_companies: int
    major_divergence_pct: float
    avg_svcii: float
    consistent_count: int
    inconclusive_count: int
    warrants_investigation_count: int
    major_divergence_count: int
