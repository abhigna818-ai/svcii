import type {
  CompanyListItem,
  SVCIIScore,
  ESGClaim,
  Facility,
  ScoreDistribution,
  SectorScore,
  Leaderboard,
  SearchResult,
  StatsResponse,
  BlogPostListItem,
  BlogPost,
  RiskAssessment,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    next: { revalidate: 3600 },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${path} → ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export function getCompanies(params?: {
  sector?: string;
  classification?: string;
  metric_type?: string;
  min_score?: number;
  max_score?: number;
}): Promise<CompanyListItem[]> {
  const qs = new URLSearchParams();
  if (params?.sector) qs.set('sector', params.sector);
  if (params?.classification) qs.set('classification', params.classification);
  if (params?.metric_type) qs.set('metric_type', params.metric_type);
  if (params?.min_score != null) qs.set('min_score', String(params.min_score));
  if (params?.max_score != null) qs.set('max_score', String(params.max_score));
  const query = qs.toString();
  return apiFetch<CompanyListItem[]>(`/api/companies${query ? `?${query}` : ''}`);
}

export function getCompany(ticker: string): Promise<SVCIIScore> {
  return apiFetch<SVCIIScore>(`/api/companies/${ticker}`);
}

export function getRisk(ticker: string): Promise<RiskAssessment> {
  return apiFetch<RiskAssessment>(`/api/companies/${ticker}/risk`);
}

export function getClaims(ticker: string): Promise<ESGClaim[]> {
  return apiFetch<ESGClaim[]>(`/api/companies/${ticker}/claims`);
}

export function getFacilities(ticker: string): Promise<Facility[]> {
  return apiFetch<Facility[]>(`/api/companies/${ticker}/facilities`);
}

export function getDistribution(): Promise<ScoreDistribution[]> {
  return apiFetch<ScoreDistribution[]>('/api/scores/distribution');
}

export function getSectorScores(): Promise<SectorScore[]> {
  return apiFetch<SectorScore[]>('/api/scores/by-sector');
}

export function getLeaderboard(): Promise<Leaderboard> {
  return apiFetch<Leaderboard>('/api/scores/leaderboard');
}

export function search(q: string): Promise<SearchResult[]> {
  return apiFetch<SearchResult[]>(`/api/search?q=${encodeURIComponent(q)}`);
}

export function getStats(): Promise<StatsResponse> {
  return apiFetch<StatsResponse>('/api/stats');
}

export function getBlogPosts(): Promise<BlogPostListItem[]> {
  return apiFetch<BlogPostListItem[]>('/api/blog/posts');
}

export function getBlogPost(slug: string): Promise<BlogPost> {
  return apiFetch<BlogPost>(`/api/blog/${slug}`);
}
