import { Suspense } from 'react';
import Link from 'next/link';
import { FileSearch, ShieldOff, Satellite, ScanSearch, Orbit, ChartBar } from 'lucide-react';
import { getStats, getLeaderboard, getBlogPosts } from '@/lib/api';
import SearchBar from '@/components/SearchBar';
import ClassificationBadge from '@/components/ClassificationBadge';
import CountUpNumber from '@/components/CountUpNumber';
import FadeUp from '@/components/FadeUp';
import dynamic from 'next/dynamic';

const ScoreTicker = dynamic(() => import('@/components/ScoreTicker'), { ssr: false });

async function HomeContent() {
  const [stats, leaderboard, posts] = await Promise.all([
    getStats().catch(() => null),
    getLeaderboard().catch(() => ({ top: [], bottom: [] })),
    getBlogPosts().catch(() => []),
  ]);

  return (
    <>
      {/* SECTION 1 — Hero (dark) */}
      <section className="section section-dark on-dark" style={{ minHeight: '92vh', display: 'flex', alignItems: 'center' }}>
        <div className="container" style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: '3rem', alignItems: 'center' }}>
          <div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', fontWeight: 600,
              letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--green-light)',
              marginBottom: '1.25rem' }}>
              Open Source · Independent · Satellite-Verified
            </div>
            <h1 style={{ marginBottom: '1.5rem', maxWidth: '600px' }}>
              Corporate ESG claims, verified from space.
            </h1>
            <p style={{ color: 'var(--text-muted-dark)', fontSize: '1.125rem', lineHeight: 1.7,
              maxWidth: '480px', marginBottom: '2rem' }}>
              SVCII cross-references sustainability disclosures against independently observable
              satellite data. Free for retail investors, researchers, and anyone who wants the truth.
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
              <Link href="/explore" className="btn btn-primary">Explore Companies</Link>
              <Link href="/methodology" style={{ color: 'var(--green-light)', fontWeight: 500 }}>
                Read the methodology →
              </Link>
            </div>
          </div>

          {stats && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div className="card card-dark">
                <CountUpNumber target={stats.total_companies}
                  className="mono" style={{ fontSize: '2.5rem', fontWeight: 700, display: 'block' }} />
                <span className="text-sm text-muted">Companies analyzed</span>
              </div>
              <div className="card card-dark">
                <CountUpNumber target={stats.avg_svcii} decimals={1}
                  className="mono" style={{ fontSize: '2.5rem', fontWeight: 700, display: 'block' }} />
                <span className="text-sm text-muted">Avg SVCII score</span>
              </div>
              <div className="card card-dark">
                <CountUpNumber target={stats.major_divergence_pct} decimals={1} suffix="%"
                  className="mono" style={{ fontSize: '2.5rem', fontWeight: 700, display: 'block', color: 'var(--classification-divergence)' }} />
                <span className="text-sm text-muted">Major divergence</span>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* SECTION 2 — Live stats ticker (beige) */}
      <section style={{ background: 'var(--bg-surface)', borderBottom: '1px solid var(--beige-warm)',
        borderTop: '1px solid var(--beige-warm)', padding: '0' }}>
        <ScoreTicker companies={[...leaderboard.top, ...leaderboard.bottom].map(c => ({
          ticker: c.ticker, name: c.name, sector: c.sector, svcii: c.svcii, classification: c.classification,
        }))} />
      </section>

      <div className="container" style={{ padding: '0 1.5rem' }}>
        <SearchBar />
      </div>

      {/* SECTION 3 — The Problem (beige) */}
      <section className="section section-light">
        <div className="container">
          <FadeUp>
            <h2 style={{ maxWidth: '640px', marginBottom: '3rem' }}>
              Retail investors are making ESG decisions on unverified data.
            </h2>
          </FadeUp>
          <FadeUp stagger>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '2.5rem' }}>
              {[
                [FileSearch, 'Companies self-report', 'Sustainability reports are written, framed, and timed by the companies they describe — with no audit standard close to what applies to financial statements.'],
                [ShieldOff, 'No independent verification', 'Commercial ESG ratings disagree with each other more often than they agree, and none of them require physical, observable proof of a claim.'],
                [Satellite, "Satellite data exists but isn't public-facing", 'The atmospheric and land-cover data needed to check many claims is freely available — but turning it into a usable comparison takes tooling most investors don\'t have.'],
              ].map(([Icon, title, desc]) => (
                <div key={title as string}>
                  {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                  {(() => { const I = Icon as any; return <I size={28} color="var(--green-deep)" strokeWidth={1.5} style={{ marginBottom: '1rem' }} />; })()}
                  <h3 style={{ marginBottom: '0.625rem' }}>{title as string}</h3>
                  <p className="text-muted" style={{ lineHeight: 1.7 }}>{desc as string}</p>
                </div>
              ))}
            </div>
          </FadeUp>
        </div>
      </section>

      {/* SECTION 4 — How it works (dark) */}
      <section className="section section-dark on-dark">
        <div className="container">
          <FadeUp>
            <h2 style={{ marginBottom: '3rem' }}>How SVCII Works</h2>
          </FadeUp>
          <FadeUp stagger>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '2.5rem', position: 'relative' }}>
              {[
                [ScanSearch, '01', 'Extract Claims', 'We parse sustainability reports using Claude to extract specific, measurable, quantified claims — not aspirational language.'],
                [Orbit, '02', 'Pull Satellite Data', 'Sentinel-5P TROPOMI and NASA VIIRS provide independent atmospheric and nighttime-lights data for the regions a claim covers.'],
                [ChartBar, '03', 'Score Divergence', 'SVCII quantifies the gap between what companies claim and what satellites observe — and shows its work either way.'],
              ].map(([Icon, num, title, desc]) => (
                <div key={num as string} style={{ borderTop: '2px solid var(--green-bright)', paddingTop: '1.5rem' }}>
                  {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                  {(() => { const I = Icon as any; return <I size={24} color="var(--green-light)" strokeWidth={1.5} style={{ marginBottom: '0.875rem' }} />; })()}
                  <div className="mono text-sm" style={{ color: 'var(--green-light)', marginBottom: '0.5rem' }}>{num as string}</div>
                  <h3 style={{ marginBottom: '0.625rem' }}>{title as string}</h3>
                  <p className="text-muted" style={{ lineHeight: 1.7 }}>{desc as string}</p>
                </div>
              ))}
            </div>
          </FadeUp>
        </div>
      </section>

      {/* SECTION 5 — Leaderboard preview (beige) */}
      <section className="section section-light">
        <div className="container">
          <FadeUp>
            <h2 style={{ marginBottom: '2.5rem' }}>Highest Divergence Companies</h2>
          </FadeUp>
          <FadeUp>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '3rem', marginBottom: '2rem' }}>
              <div>
                <div className="mono text-sm" style={{ color: 'var(--classification-divergence)', marginBottom: '1rem', fontWeight: 600 }}>
                  MOST DIVERGENT
                </div>
                <table>
                  <tbody>
                    {leaderboard.bottom.slice(0, 5).map(c => (
                      <tr key={c.ticker}>
                        <td className="mono" style={{ fontWeight: 600 }}>{c.ticker}</td>
                        <td>{c.name}</td>
                        <td className="mono" style={{ textAlign: 'right' }}>{c.svcii.toFixed(1)}</td>
                        <td><ClassificationBadge classification={c.classification} size="sm" /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div>
                <div className="mono text-sm" style={{ color: 'var(--classification-consistent)', marginBottom: '1rem', fontWeight: 600 }}>
                  MOST CONSISTENT
                </div>
                <table>
                  <tbody>
                    {leaderboard.top.slice(0, 5).map(c => (
                      <tr key={c.ticker}>
                        <td className="mono" style={{ fontWeight: 600 }}>{c.ticker}</td>
                        <td>{c.name}</td>
                        <td className="mono" style={{ textAlign: 'right' }}>{c.svcii.toFixed(1)}</td>
                        <td><ClassificationBadge classification={c.classification} size="sm" /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <Link href="/explore" style={{ fontWeight: 600 }}>View all companies →</Link>
          </FadeUp>
        </div>
      </section>

      {/* SECTION 6 — Featured blog posts (dark) */}
      {posts.length > 0 && (
        <section className="section section-dark on-dark">
          <div className="container">
            <FadeUp>
              <h2 style={{ marginBottom: '2.5rem' }}>Research &amp; Analysis</h2>
            </FadeUp>
            <FadeUp stagger>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.75rem' }}>
                {posts.slice(0, 3).map(p => (
                  <Link key={p.slug} href={`/blog/${p.slug}`} style={{ textDecoration: 'none' }}>
                    <div className="card card-dark" style={{ height: '100%' }}>
                      <div className="mono text-xs" style={{ color: 'var(--green-light)', textTransform: 'uppercase',
                        letterSpacing: '0.06em', marginBottom: '0.75rem' }}>
                        {p.category}
                      </div>
                      <h3 style={{ fontFamily: 'var(--font-serif)', marginBottom: '0.75rem', lineHeight: 1.3 }}>
                        {p.title}
                      </h3>
                      <p className="text-muted text-sm" style={{ lineHeight: 1.65, marginBottom: '1rem' }}>
                        {p.excerpt}
                      </p>
                      <span style={{ color: 'var(--green-light)', fontSize: '0.875rem', fontWeight: 500 }}>Read →</span>
                    </div>
                  </Link>
                ))}
              </div>
            </FadeUp>
          </div>
        </section>
      )}

      {/* SECTION 7 — Data sources (beige) */}
      <section className="section section-light">
        <div className="container">
          <FadeUp>
            <h2 style={{ marginBottom: '2.5rem' }}>Built on public data</h2>
          </FadeUp>
          <FadeUp stagger>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '2rem' }}>
              {[
                ['ESA Sentinel-5P', 'Atmospheric methane (XCH4) via the TROPOMI instrument.'],
                ['NASA VIIRS', 'Nighttime lights — a proxy for nearby economic activity.'],
                ['EPA GHGRP', 'Facility-level greenhouse gas reporting in the US.'],
                ['ESA WorldCover', '10m global land cover classification.'],
              ].map(([name, desc]) => (
                <div key={name}>
                  <div className="mono" style={{ fontWeight: 600, marginBottom: '0.5rem' }}>{name}</div>
                  <p className="text-muted text-sm" style={{ lineHeight: 1.65 }}>{desc}</p>
                </div>
              ))}
            </div>
          </FadeUp>
        </div>
      </section>
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
