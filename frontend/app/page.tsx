import { Suspense } from 'react';
import { getStats, getSectorScores, getLeaderboard, getCompanies, getDistribution } from '@/lib/api';
import SearchBar from '@/components/SearchBar';
import SectorGrid from '@/components/SectorGrid';
import CompanyCard from '@/components/CompanyCard';
import dynamic from 'next/dynamic';

const ScoreTicker   = dynamic(() => import('@/components/ScoreTicker'),       { ssr: false });
const AnimatedScore = dynamic(() => import('@/components/AnimatedScore'),      { ssr: false });
const DistChart     = dynamic(() => import('@/components/DistributionChart'),  { ssr: false });

async function HomeContent() {
  const [stats, sectors, leaderboard, allCompanies, dist] = await Promise.all([
    getStats().catch(() => null),
    getSectorScores().catch(() => []),
    getLeaderboard().catch(() => ({ top: [], bottom: [] })),
    getCompanies().catch(() => []),
    getDistribution().catch(() => []),
  ]);

  const date = new Date().toLocaleDateString('en-GB', {
    day: 'numeric', month: 'long', year: 'numeric',
  });

  return (
    <>
      {/* Masthead dateline */}
      <div style={{ borderBottom: '1px solid var(--border)', padding: '0.625rem 1.5rem',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        maxWidth: '1200px', margin: '0 auto' }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.5625rem',
          color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
          Satellite data vintage: 2021–2023 · EPA GHGRP 2022 · ESG reports 2023
        </span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.5625rem', color: 'var(--text-muted)' }}>
          {date}
        </span>
      </div>

      {/* Hero */}
      <div style={{ padding: '3.5rem 1.5rem 2.5rem', maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '3rem',
          alignItems: 'end', marginBottom: '2.5rem' }}>

          <div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.5625rem', fontWeight: 600,
              letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--green-primary)',
              marginBottom: '0.75rem' }}>
              Open-source · Free for retail investors · MIT licensed
            </div>
            <h1 style={{ fontSize: 'clamp(2rem, 5vw, 3.25rem)', lineHeight: 1.1,
              marginBottom: '1.25rem', maxWidth: '560px' }}>
              Satellite data doesn&apos;t lie.
            </h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9375rem', lineHeight: 1.75,
              maxWidth: '520px' }}>
              SVCII cross-references corporate ESG claims against independently observable
              satellite data. Free. Open source. No fund affiliation.
            </p>
          </div>

          {/* Live stats */}
          {stats && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', flexShrink: 0,
              borderLeft: '3px solid var(--green-primary)', paddingLeft: '1.5rem', minWidth: '180px' }}>
              <div>
                <AnimatedScore
                  target={stats.total_companies}
                  decimals={0}
                  style={{ fontFamily: 'var(--font-sans)', fontSize: '2.75rem',
                    fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1, display: 'block' }}
                />
                <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>companies analysed</span>
              </div>
              <div>
                <AnimatedScore
                  target={stats.major_divergence_pct}
                  decimals={1}
                  suffix="%"
                  style={{ fontFamily: 'var(--font-sans)', fontSize: '2.75rem',
                    fontWeight: 700, color: 'var(--red)', lineHeight: 1, display: 'block' }}
                />
                <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>major divergence</span>
              </div>
              <div>
                <AnimatedScore
                  target={stats.avg_svcii}
                  decimals={1}
                  style={{ fontFamily: 'var(--font-sans)', fontSize: '2.75rem',
                    fontWeight: 700, color: 'var(--orange)', lineHeight: 1, display: 'block' }}
                />
                <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>avg SVCII score</span>
              </div>
              <div>
                <AnimatedScore
                  target={stats.claims_verified ?? 0}
                  decimals={0}
                  style={{ fontFamily: 'var(--font-sans)', fontSize: '2.75rem',
                    fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1, display: 'block' }}
                />
                <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>claims verified</span>
              </div>
            </div>
          )}
        </div>

        <SearchBar />
      </div>

      {/* Company score ticker */}
      {allCompanies.length > 0 && <ScoreTicker companies={allCompanies} />}

      <div className="container" style={{ paddingTop: '3rem', paddingBottom: '4rem' }}>

        {/* Distribution + Sectors */}
        <div style={{ display: 'grid', gridTemplateColumns: '5fr 7fr', gap: '3rem',
          marginBottom: '3.5rem', alignItems: 'start' }}>
          {dist.length > 0 && (
            <div>
              <div className="section-label">Score distribution</div>
              <DistChart data={dist} />
              <p style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginTop: '0.75rem',
                lineHeight: 1.65 }}>
                Distribution of SVCII scores. Scores below 40 indicate satellite data significantly
                contradicts stated ESG claims. Above 80 = satellite-consistent.
              </p>
            </div>
          )}
          {sectors.length > 0 && (
            <div>
              <div className="section-label">Average score by sector</div>
              <SectorGrid sectors={sectors} />
            </div>
          )}
        </div>

        {/* Leaderboard */}
        {(leaderboard.top.length > 0 || leaderboard.bottom.length > 0) && (
          <>
            <div className="section-label">Performance index</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '3rem',
              marginBottom: '3rem' }}>
              {leaderboard.top.length > 0 && (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem',
                    marginBottom: '0.875rem' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.5625rem',
                      fontWeight: 600, letterSpacing: '0.12em', textTransform: 'uppercase',
                      color: 'var(--green-primary)', whiteSpace: 'nowrap' }}>
                      ● Most consistent
                    </span>
                    <div style={{ flex: 1, height: '1px', background: 'var(--border)' }} />
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                    {leaderboard.top.slice(0, 5).map((c, i) => (
                      <CompanyCard key={c.ticker} company={c} rank={i + 1} />
                    ))}
                  </div>
                </div>
              )}
              {leaderboard.bottom.length > 0 && (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem',
                    marginBottom: '0.875rem' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.5625rem',
                      fontWeight: 600, letterSpacing: '0.12em', textTransform: 'uppercase',
                      color: 'var(--red)', whiteSpace: 'nowrap' }}>
                      ● Most divergent
                    </span>
                    <div style={{ flex: 1, height: '1px', background: 'var(--border)' }} />
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                    {leaderboard.bottom.slice(0, 5).map((c, i) => (
                      <CompanyCard key={c.ticker} company={c} rank={i + 1} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </>
        )}

        {/* Editorial footer note */}
        <div style={{ borderTop: '3px solid var(--green-primary)', paddingTop: '1.5rem',
          display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
          <div>
            <div style={{ fontFamily: 'var(--font-sans)', fontSize: '1rem', fontWeight: 600,
              marginBottom: '0.5rem' }}>On the data</div>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', lineHeight: 1.75 }}>
              ESG claim text is sourced verbatim from 2023 corporate sustainability reports.
              Satellite readings derive from ESA Sentinel-5P TROPOMI (methane), NASA VIIRS
              Black Marble (nighttime lights), and ESA WorldCover (land cover). Scores are
              correlational — elevated XCH₄ near a facility does not prove causation.
            </p>
          </div>
          <div>
            <div style={{ fontFamily: 'var(--font-sans)', fontSize: '1rem', fontWeight: 600,
              marginBottom: '0.5rem' }}>On the methodology</div>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', lineHeight: 1.75 }}>
              The SVCII formula weights four components: trend direction (40 pts), magnitude
              proportionality (30 pts), temporal consistency (20 pts), and disclosure quality
              (10 pts). Intensity-based claims receive an additional −10 penalty. E and S scores
              combine 60/40.{' '}
              <a href="/methodology">Full methodology →</a>
            </p>
          </div>
        </div>
      </div>
    </>
  );
}

export default function HomePage() {
  return (
    <Suspense fallback={
      <div style={{ padding: '4rem 1.5rem' }}>
        <div className="skeleton" style={{ height: '3rem', width: '500px', marginBottom: '1rem' }} />
        <div className="skeleton" style={{ height: '1rem', width: '300px', marginBottom: '2rem' }} />
        <div className="skeleton" style={{ height: '3.5rem', maxWidth: '640px' }} />
      </div>
    }>
      <HomeContent />
    </Suspense>
  );
}
