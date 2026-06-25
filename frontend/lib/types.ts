export type Classification =
  | 'CONSISTENT'
  | 'INCONCLUSIVE'
  | 'WARRANTS INVESTIGATION'
  | 'MAJOR DIVERGENCE';

export type MetricType = 'absolute' | 'intensity' | 'ambiguous';
export type SatelliteConsistency = 'consistent' | 'divergent' | 'inconclusive';

export interface EScoreComponents {
  trend_direction: number;
  magnitude: number;
  temporal: number;
  disclosure: number;
}

export interface EScore {
  e_score: number;
  components: EScoreComponents;
  divergence_pct: number | null;
  metric_type: MetricType | null;
  satellite_source: string;
}

export interface SScoreComponents {
  land_integrity: number;
  community_prosperity: number;
  supply_chain: number;
}

export interface SScoreWeights {
  w_land: number;
  w_community: number;
  w_supply: number;
}

export interface SScore {
  s_score: number | null;
  components: SScoreComponents | null;
  weights: SScoreWeights | null;
  satellite_sources: string[];
  reason: string | null;
}

export interface SVCIIScore {
  ticker: string;
  svcii: number | null;
  e_score: EScore | null;
  s_score: SScore | null;
  classification: Classification | null;
  methodology: string | null;
  last_updated: string | null;
  data_vintage: string;
}

export interface CompanyListItem {
  ticker: string;
  name: string;
  sector: string | null;
  industry: string | null;
  market_cap_b: number | null;
  msci_esg_rating: string | null;
  svcii: number | null;
  e_score: number | null;
  s_score: number | null;
  classification: Classification | null;
}

export interface ESGClaim {
  id: number;
  ticker: string;
  claim_text: string;
  category: string | null;
  subcategory: string | null;
  metric_type: MetricType | null;
  baseline_year: number | null;
  target_year: number | null;
  magnitude_pct: number | null;
  source_doc: string | null;
  page_number: number | null;
  satellite_consistent: SatelliteConsistency | null;
}

export interface Facility {
  id: number;
  ticker: string;
  facility_name: string;
  latitude: number;
  longitude: number;
  operation_type: string | null;
  country: string | null;
  region: string | null;
  xch4_value: number | null;
  xch4_trend: number | null;
  ntl_value: number | null;
}

export interface ScoreDistribution {
  bucket_start: number;
  bucket_end: number;
  count: number;
  label: string;
}

export interface SectorScore {
  sector: string;
  avg_svcii: number;
  avg_e_score: number;
  avg_s_score: number | null;
  company_count: number;
  consistent_count: number;
  divergent_count: number;
}

export interface LeaderboardEntry {
  ticker: string;
  name: string;
  sector: string | null;
  svcii: number;
  classification: Classification;
}

export interface Leaderboard {
  top: LeaderboardEntry[];
  bottom: LeaderboardEntry[];
}

export interface SearchResult {
  ticker: string;
  name: string;
  sector: string | null;
  svcii: number | null;
  classification: Classification | null;
}

export interface StatsResponse {
  total_companies: number;
  major_divergence_pct: number;
  avg_svcii: number;
  consistent_count: number;
  inconclusive_count: number;
  warrants_investigation_count: number;
  major_divergence_count: number;
  claims_verified: number;
}

export interface BlogPostListItem {
  slug: string;
  title: string;
  excerpt: string | null;
  author: string | null;
  published_at: string | null;
  category: string | null;
  ticker_mentioned: string | null;
}

export interface BlogPost extends BlogPostListItem {
  content_md: string;
}

export interface RiskAssessment {
  ticker: string;
  regulatory_risk: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  risk_factors: string[];
  esg_fund_exposure_note: string;
  satellite_vs_claim_summary: string;
}
