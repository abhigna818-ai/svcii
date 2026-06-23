import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { Suspense } from 'react';
import { getCompany, getClaims, getFacilities } from '@/lib/api';
import ScoreDisplay from '@/components/ScoreDisplay';
import ScoreBar from '@/components/ScoreBar';
import ClaimCard from '@/components/ClaimCard';
import type { SVCIIScore, ESGClaim, Facility } from '@/lib/types';
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
    return { bg: 'rgba(56,102,65,0.08)', border: 'var(--green-primary)', text: 'var(--green-primary)',
      blurb: 'Satellite data is directionally consistent with this company\'s ESG claims across all scored components.' };
  if (c === 'MAJOR DIVERGENCE')
    return { bg: 'rgba(193,18,31,0.07)', border: 'var(--red)', text: 'var(--red)',
      blurb: 'Satellite observations significantly contradict this company\'s stated ESG trajectory. Claims warrant independent scrutiny.' };
  if (c === 'WARRANTS INVESTIGATION')
    return { bg: 'rgba(231,111,0,0.08)', border: 'var(--orange)', text: 'var(--orange)',
      blurb: 'Notable divergence between claimed and observed trends. Signals require closer examination before accepting claims at face value.' };
  return { bg: 'rgba(231,111,0,0.06)', border: 'var(--orange)', text: 'var(--orange)',
    blurb: 'Mixed signals. The directional trend is broadly aligned but magnitude or temporal discrepancies prevent a definitive verdict.' };
}

async function CompanyContent({ ticker }: { ticker: string }) {
  let score: SVCIIScore;
  let claims: ESGClaim[] = [];
  let facilities: Facility[] = [];

  try {
    [score, claims, facilities] = await Promise.all([
      getCompany(ticker),
      getClaims(ticker).catch(() => []),
      getFacilities(ticker).catch(() => []),
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
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 1.5rem' }}>

      {/* Classification banner */}
      <div style={{ background: meta.bg, borderLeft: `3px solid ${meta.border}`,
        padding: '0.875rem 1.25rem', margin: '1.5rem 0', display: 'flex',
        gap: '1rem', alignItems: 'flex-start' }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.625rem', fontWeight: 600,
          letterSpacing: '0.12em', textTransform: 'uppercase', color: meta.text,
          whiteSpace: 'nowrap', marginTop: '0.2rem' }}>
          {score.classification}
        </span>
        <p style={{ fontSize: '0.8125rem', color: 'var(--text-primary)', lineHeight: 1.6, margin: 0 }}>
          {meta.blurb}
        </p>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.5625rem', color: 'var(--text-muted)',
          whiteSpace: 'nowrap', marginTop: '0.25rem', marginLeft: 'auto' }}>
          {score.data_vintage}
        </span>
      </div>

      {/* Company header */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '2rem',
        alignItems: 'start', paddingBottom: '2rem', borderBottom: '1px solid var(--border)' }}>
        <div>
          <h1 style={{ fontSize: 'clamp(1.5rem, 4vw, 2.25rem)', marginBottom: '0.25rem' }}>
            {ticker}
          </h1>
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {score.methodology}
          </p>
        </div>
        <ScoreDisplay score={score.svcii} classification={score.classification} label="SVCII" size="lg" />
      </div>

      {/* Main two-column layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: '3rem',
        paddingTop: '2rem', alignItems: 'start' }}>

        {/* LEFT — scores & claims */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2.5rem' }}>

          {/* E + S score summary row */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2px',
            background: 'var(--border)', border: '1px solid var(--border)',
            borderRadius: '2px', overflow: 'hidden' }}>
            <div style={{ background: 'var(--bg-elevated)', padding: '1.25rem' }}>
              <div style={{ fontSize: '0.5625rem', fontWeight: 600, letterSpacing: '0.12em',
                textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                E Score — Environmental
              </div>
              <div style={{ fontFamily: 'var(--font-sans)', fontSize: '2.5rem', fontWeight: 700,
                color: 'var(--text-primary)', lineHeight: 1, marginBottom: '0.25rem' }}>
                {score.e_score?.e_score.toFixed(1) ?? '—'}
              </div>
              <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                {score.e_score?.metric_type?.toUpperCase()} basis ·{' '}
                Sentinel-5P TROPOMI
              </div>
            </div>
            <div style={{ background: 'var(--bg-elevated)', padding: '1.25rem' }}>
              <div style={{ fontSize: '0.5625rem', fontWeight: 600, letterSpacing: '0.12em',
                textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                S Score — Social
              </div>
              <div style={{ fontFamily: 'var(--font-sans)', fontSize: '2.5rem', fontWeight: 700,
                color: 'var(--text-primary)', lineHeight: 1, marginBottom: '0.25rem' }}>
                {score.s_score?.s_score?.toFixed(1) ?? '—'}
              </div>
              <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
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
                <ScoreBar label="Trend Direction Agreement" value={score.e_score.components.trend_direction} max={40} color="var(--green-primary)" />
                <ScoreBar label="Magnitude Proportionality" value={score.e_score.components.magnitude} max={30} color="var(--green-primary)" />
                <ScoreBar label="Temporal Consistency" value={score.e_score.components.temporal} max={20} color="var(--green-primary)" />
                <ScoreBar label="Disclosure Quality" value={score.e_score.components.disclosure} max={10} color="var(--green-glow)" />
              </div>
              <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.5625rem', color: 'var(--text-muted)' }}>
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
                <ScoreBar label="Land Integrity" value={score.s_score.components.land_integrity} max={100} color="var(--green-glow)" />
                <ScoreBar label="Community Prosperity" value={score.s_score.components.community_prosperity} max={100} color="var(--green-glow)" />
                <ScoreBar label="Supply Chain Land Use" value={score.s_score.components.supply_chain} max={100} color="var(--green-glow)" />
              </div>
              <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.5625rem', color: 'var(--text-muted)' }}>
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
                    letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-muted)',
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
                    letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-muted)',
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
              <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)',
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
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.5625rem', color: 'var(--text-muted)',
              marginTop: '0.375rem' }}>
              Dot colour = atmospheric XCH₄ trend · Sentinel-5P, 2021–2023
            </p>
          </div>

          {/* Satellite table */}
          {facilities.length > 0 && (
            <div>
              <div className="section-label">Satellite readings</div>
              <div style={{ overflowX: 'auto', border: '1px solid var(--border)',
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
                          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.5rem', color: 'var(--text-muted)' }}>
                            {f.latitude.toFixed(2)}°, {f.longitude.toFixed(2)}°
                          </div>
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)', textAlign: 'right' }}>
                          {f.xch4_value != null ? f.xch4_value.toFixed(1) : '—'}
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)', textAlign: 'right',
                          color: f.xch4_trend == null ? 'var(--text-muted)'
                            : f.xch4_trend < -1 ? 'var(--green-primary)'
                            : f.xch4_trend > 1 ? 'var(--red)' : 'var(--orange)' }}>
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

      <div style={{ height: '4rem' }} />
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
