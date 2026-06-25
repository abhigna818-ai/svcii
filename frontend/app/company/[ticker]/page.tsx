import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { Suspense } from 'react';
import { getCompany, getClaims, getFacilities, getRisk } from '@/lib/api';
import ScoreDisplay from '@/components/ScoreDisplay';
import ScoreBar from '@/components/ScoreBar';
import ClaimCard from '@/components/ClaimCard';
import type { SVCIIScore, ESGClaim, Facility, RiskAssessment } from '@/lib/types';
import dynamic from 'next/dynamic';

const FacilityMap    = dynamic(() => import('@/components/FacilityMap'),     { ssr: false });
const RadarChart     = dynamic(() => import('@/components/ScoreRadarChart'),  { ssr: false });
const DivergenceMeter= dynamic(() => import('@/components/DivergenceMeter'), { ssr: false });

interface Props {
  params: Promise<{ ticker: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { ticker } = await params;
  try {
    const score = await getCompany(ticker.toUpperCase());
    return {
      title: `${score.ticker} — SVCII ${score.svcii?.toFixed(1) ?? 'N/A'}`,
      description: `SVCII satellite-verified ESG score for ${score.ticker}: ${score.svcii?.toFixed(1)} (${score.classification})`,
    };
  } catch {
    return { title: ticker.toUpperCase() };
  }
}

function classificationMeta(c: string | null): { bg: string; border: string; text: string; blurb: string } {
  if (c === 'CONSISTENT')
    return { bg: 'rgba(56,102,65,0.08)', border: 'var(--green-deep)', text: 'var(--green-deep)',
      blurb: 'Satellite data is directionally consistent with this company\'s ESG claims across all scored components.' };
  if (c === 'MAJOR DIVERGENCE')
    return { bg: 'rgba(193,18,31,0.07)', border: 'var(--classification-divergence)', text: 'var(--classification-divergence)',
      blurb: 'Satellite observations significantly contradict this company\'s stated ESG trajectory. Claims warrant independent scrutiny.' };
  if (c === 'WARRANTS INVESTIGATION')
    return { bg: 'rgba(231,111,0,0.08)', border: 'var(--classification-warrants)', text: 'var(--classification-warrants)',
      blurb: 'Notable divergence between claimed and observed trends. Signals require closer examination before accepting claims at face value.' };
  return { bg: 'rgba(231,111,0,0.06)', border: 'var(--classification-warrants)', text: 'var(--classification-warrants)',
    blurb: 'Mixed signals. The directional trend is broadly aligned but magnitude or temporal discrepancies prevent a definitive verdict.' };
}

function riskColor(level: string | undefined): string {
  if (level === 'CRITICAL' || level === 'HIGH') return 'var(--classification-divergence)';
  if (level === 'MEDIUM') return 'var(--classification-warrants)';
  return 'var(--classification-consistent)';
}

async function CompanyContent({ ticker }: { ticker: string }) {
  let score: SVCIIScore;
  let claims: ESGClaim[] = [];
  let facilities: Facility[] = [];
  let risk: RiskAssessment | null = null;

  try {
    [score, claims, facilities, risk] = await Promise.all([
      getCompany(ticker),
      getClaims(ticker).catch(() => []),
      getFacilities(ticker).catch(() => []),
      getRisk(ticker).catch(() => null),
    ]);
  } catch {
    notFound();
  }

  const meta = classificationMeta(score.classification);
  const envClaims    = claims.filter(c => c.category === 'environmental');
  const socialClaims = claims.filter(c => c.category === 'social');

  // Approximate observed pct from divergence + claimed
  const claimedMag = claims.find(c => c.magnitude_pct != null)?.magnitude_pct ?? 0;
  const divergence  = score.e_score?.divergence_pct ?? 0;
  const trendDir    = score.e_score?.components?.trend_direction ?? 0;
  // observed direction: if trend==40 => same as claimed; if 0 => opposite
  const observedSign = trendDir >= 40 ? Math.sign(claimedMag) : trendDir === 20 ? 0 : -Math.sign(claimedMag);
  const observedMag = observedSign * Math.abs(Math.abs(claimedMag) - divergence);

  return (
    <div>
      {/* Company header (dark band) */}
      <div className="section-dark on-dark" style={{ padding: '3rem 1.5rem 2rem' }}>
        <div className="container" style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '2rem',
          alignItems: 'start' }}>
          <div>
            <h1 className="mono" style={{ fontSize: 'clamp(1.75rem, 4vw, 2.5rem)', marginBottom: '0.25rem',
              fontFamily: 'var(--font-mono)' }}>
              {ticker}
            </h1>
            <p style={{ color: 'var(--text-muted-dark)', fontSize: '0.9375rem' }}>
              {score.methodology}
            </p>
          </div>
          <ScoreDisplay score={score.svcii} classification={score.classification} label="SVCII" size="lg" />
        </div>
      </div>

      {/* Classification banner */}
      <div className="container" style={{ padding: '0 1.5rem' }}>
        <div style={{ background: meta.bg, borderLeft: `3px solid ${meta.border}`,
          padding: '0.875rem 1.25rem', margin: '1.5rem 0', display: 'flex',
          gap: '1rem', alignItems: 'flex-start' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.625rem', fontWeight: 600,
            letterSpacing: '0.12em', textTransform: 'uppercase', color: meta.text,
            whiteSpace: 'nowrap', marginTop: '0.2rem' }}>
            {score.classification}
          </span>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-dark)', lineHeight: 1.6, margin: 0 }}>
            {meta.blurb}
          </p>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.5625rem', color: 'var(--text-muted-light)',
            whiteSpace: 'nowrap', marginTop: '0.25rem', marginLeft: 'auto' }}>
            {score.data_vintage}
          </span>
        </div>

      {/* Main two-column layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: '3rem',
        paddingTop: '1rem', paddingBottom: '2rem', alignItems: 'start' }}>

        {/* LEFT — scores & claims */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2.5rem' }}>

          {/* E + S score summary row */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2px',
            background: 'var(--beige-warm)', border: '1px solid var(--beige-warm)',
            borderRadius: '2px', overflow: 'hidden' }}>
            <div style={{ background: 'var(--bg-surface)', padding: '1.25rem' }}>
              <div style={{ fontSize: '0.5625rem', fontWeight: 600, letterSpacing: '0.12em',
                textTransform: 'uppercase', color: 'var(--text-muted-light)', marginBottom: '0.5rem' }}>
                E Score — Environmental
              </div>
              <div style={{ fontFamily: 'var(--font-sans)', fontSize: '2.5rem', fontWeight: 700,
                color: 'var(--text-dark)', lineHeight: 1, marginBottom: '0.25rem' }}>
                {score.e_score?.e_score.toFixed(1) ?? '—'}
              </div>
              <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted-light)' }}>
                {score.e_score?.metric_type?.toUpperCase()} basis ·{' '}
                Sentinel-5P TROPOMI
              </div>
            </div>
            <div style={{ background: 'var(--bg-surface)', padding: '1.25rem' }}>
              <div style={{ fontSize: '0.5625rem', fontWeight: 600, letterSpacing: '0.12em',
                textTransform: 'uppercase', color: 'var(--text-muted-light)', marginBottom: '0.5rem' }}>
                S Score — Social
              </div>
              <div style={{ fontFamily: 'var(--font-sans)', fontSize: '2.5rem', fontWeight: 700,
                color: 'var(--text-dark)', lineHeight: 1, marginBottom: '0.25rem' }}>
                {score.s_score?.s_score?.toFixed(1) ?? '—'}
              </div>
              <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted-light)' }}>
                {score.s_score?.s_score != null
                  ? 'WorldCover · VIIRS Black Marble'
                  : score.s_score?.reason ?? 'No verifiable social claims'}
              </div>
            </div>
          </div>

          {/* Divergence meter */}
          {score.e_score && claimedMag !== 0 && (
            <div>
              <div className="section-label">Claim vs. satellite divergence</div>
              <DivergenceMeter
                claimed={claimedMag}
                observed={observedMag}
                metricType={score.e_score.metric_type}
              />
            </div>
          )}

          {/* E Score component bars */}
          {score.e_score && (
            <div>
              <div className="section-label">E Score breakdown</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem',
                marginBottom: '0.75rem' }}>
                <ScoreBar label="Trend Direction Agreement" value={score.e_score.components.trend_direction} max={40} color="var(--green-deep)" />
                <ScoreBar label="Magnitude Proportionality" value={score.e_score.components.magnitude} max={30} color="var(--green-deep)" />
                <ScoreBar label="Temporal Consistency" value={score.e_score.components.temporal} max={20} color="var(--green-deep)" />
                <ScoreBar label="Disclosure Quality" value={score.e_score.components.disclosure} max={10} color="var(--green-bright)" />
              </div>
              <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.5625rem', color: 'var(--text-muted-light)' }}>
                Source: {score.e_score.satellite_source}
              </p>
            </div>
          )}

          {/* S Score component bars */}
          {score.s_score?.s_score != null && score.s_score.components && (
            <div>
              <div className="section-label">S Score breakdown</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem',
                marginBottom: '0.75rem' }}>
                <ScoreBar label="Land Integrity" value={score.s_score.components.land_integrity} max={100} color="var(--green-bright)" />
                <ScoreBar label="Community Prosperity" value={score.s_score.components.community_prosperity} max={100} color="var(--green-bright)" />
                <ScoreBar label="Supply Chain Land Use" value={score.s_score.components.supply_chain} max={100} color="var(--green-bright)" />
              </div>
              <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.5625rem', color: 'var(--text-muted-light)' }}>
                Sources: ESA WorldCover 2020/2021 · NASA VIIRS Black Marble VNP46A2
              </p>
            </div>
          )}

          {/* ESG Claims */}
          {claims.length > 0 && (
            <div>
              <div className="section-label">
                ESG claims ({claims.length} total · {envClaims.length} environmental · {socialClaims.length} social)
              </div>

              {envClaims.length > 0 && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.5625rem', fontWeight: 600,
                    letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-muted-light)',
                    marginBottom: '0.75rem' }}>
                    Environmental
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {envClaims.map(c => <ClaimCard key={c.id} claim={c} />)}
                  </div>
                </div>
              )}
              {socialClaims.length > 0 && (
                <div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.5625rem', fontWeight: 600,
                    letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-muted-light)',
                    marginBottom: '0.75rem' }}>
                    Social
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {socialClaims.map(c => <ClaimCard key={c.id} claim={c} />)}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* RIGHT — map + radar + table */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem',
          position: 'sticky', top: '5rem' }}>

          {/* Radar chart */}
          {score.e_score && (
            <div>
              <div className="section-label">Score components</div>
              <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--beige-warm)',
                borderRadius: '2px', padding: '0.5rem' }}>
                <RadarChart
                  eScore={score.e_score.e_score}
                  sScore={score.s_score?.s_score ?? null}
                  trendDirection={score.e_score.components.trend_direction}
                  magnitude={score.e_score.components.magnitude}
                  temporal={score.e_score.components.temporal}
                  disclosure={score.e_score.components.disclosure}
                />
              </div>
            </div>
          )}

          {/* Map */}
          <div>
            <div className="section-label">
              Facility locations ({facilities.length})
            </div>
            <FacilityMap facilities={facilities} height={280} />
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.5625rem', color: 'var(--text-muted-light)',
              marginTop: '0.375rem' }}>
              Dot colour = atmospheric XCH₄ trend · Sentinel-5P, 2021–2023
            </p>
          </div>

          {/* Satellite table */}
          {facilities.length > 0 && (
            <div>
              <div className="section-label">Satellite readings</div>
              <div style={{ overflowX: 'auto', border: '1px solid var(--beige-warm)',
                borderRadius: '2px', overflow: 'hidden' }}>
                <table style={{ fontSize: '0.6875rem' }}>
                  <thead>
                    <tr>
                      <th style={{ fontSize: '0.5rem' }}>Facility</th>
                      <th style={{ fontSize: '0.5rem', textAlign: 'right' }}>XCH₄ ppb</th>
                      <th style={{ fontSize: '0.5rem', textAlign: 'right' }}>Trend %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {facilities.map(f => (
                      <tr key={f.id}>
                        <td>
                          <div style={{ fontWeight: 500, maxWidth: '130px', overflow: 'hidden',
                            textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.facility_name}</div>
                          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.5rem', color: 'var(--text-muted-light)' }}>
                            {f.latitude.toFixed(2)}°, {f.longitude.toFixed(2)}°
                          </div>
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)', textAlign: 'right' }}>
                          {f.xch4_value != null ? f.xch4_value.toFixed(1) : '—'}
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)', textAlign: 'right',
                          color: f.xch4_trend == null ? 'var(--text-muted-light)'
                            : f.xch4_trend < -1 ? 'var(--green-deep)'
                            : f.xch4_trend > 1 ? 'var(--classification-divergence)' : 'var(--classification-warrants)' }}>
                          {f.xch4_trend != null
                            ? `${f.xch4_trend > 0 ? '+' : ''}${f.xch4_trend.toFixed(2)}`
                            : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
      </div>

      {/* Investor Risk (dark band) */}
      {risk && (
        <div className="section-dark on-dark" style={{ padding: '3rem 1.5rem' }}>
          <div className="container">
            <div className="section-label">Investor Risk</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
              <span className="badge" style={{ background: riskColor(risk.regulatory_risk) }}>
                {risk.regulatory_risk} RISK
              </span>
              <span className="text-muted text-sm">{risk.satellite_vs_claim_summary}</span>
            </div>

            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.625rem',
              marginBottom: '2rem' }}>
              {risk.risk_factors.map((f, i) => (
                <li key={i} style={{ display: 'flex', gap: '0.75rem' }}>
                  <span style={{ color: 'var(--green-bright)', flexShrink: 0 }}>—</span>
                  <span style={{ color: 'var(--text-muted-dark)', lineHeight: 1.7 }}>{f}</span>
                </li>
              ))}
            </ul>

            <blockquote className="pull-quote" style={{ color: 'var(--text-light)' }}>
              {risk.esg_fund_exposure_note}
            </blockquote>
          </div>
        </div>
      )}

      <div className="section section-light" style={{ paddingTop: '1.5rem', paddingBottom: '1.5rem' }}>
        <div className="container">
          <p className="text-sm text-muted">
            Read the full <a href="/methodology">methodology →</a>
          </p>
        </div>
      </div>
    </div>
  );
}

export default async function CompanyPage({ params }: Props) {
  const { ticker } = await params;
  return (
    <Suspense fallback={
      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '2.5rem 1.5rem' }}>
        <div className="skeleton" style={{ height: '4rem', marginBottom: '1rem' }} />
        <div style={{ display: 'flex', gap: '1rem', flexDirection: 'column' }}>
          {[1,2,3,4].map(i => <div key={i} className="skeleton" style={{ height: '60px' }} />)}
        </div>
      </div>
    }>
      <CompanyContent ticker={ticker.toUpperCase()} />
    </Suspense>
  );
}
