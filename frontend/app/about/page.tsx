'use client';
import Link from 'next/link';

export default function AboutPage() {
  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 1.5rem',
      paddingTop: '3rem', paddingBottom: '5rem' }}>

      {/* Founder */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4rem',
        alignItems: 'start', marginBottom: '4rem', paddingBottom: '4rem',
        borderBottom: '1px solid var(--paper-3)' }}>

        <div>
          <div style={{ width: '56px', height: '56px', borderRadius: '2px',
            background: 'var(--accent)', display: 'flex', alignItems: 'center',
            justifyContent: 'center', marginBottom: '1.25rem' }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem',
              fontWeight: 700, color: 'var(--paper)' }}>A</span>
          </div>

          <h1 style={{ fontSize: '2rem', lineHeight: 1.1, marginBottom: '0.375rem' }}>
            Abhigna Naik
          </h1>
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem',
            color: 'var(--muted)', marginBottom: '1.5rem' }}>
            High school student · Hyderabad, India
          </p>

          <p style={{ fontSize: '0.9375rem', lineHeight: 1.8, color: 'var(--muted)' }}>
            I got tired of seeing companies claim they were getting greener while
            nothing seemed to change. Built SVCII to make it easy for anyone to
            check those claims against satellite data — no finance background needed.
          </p>
        </div>

        <div style={{ borderLeft: '3px solid var(--accent)', paddingLeft: '2rem',
          marginTop: '0.5rem' }}>
          <blockquote style={{ fontFamily: 'var(--font-display)',
            fontSize: 'clamp(1.1rem, 2vw, 1.375rem)',
            lineHeight: 1.6, color: 'var(--ink)', fontStyle: 'italic',
            marginBottom: '1rem' }}>
            "Companies say a lot of things in their sustainability reports.
            Satellites don't."
          </blockquote>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.6875rem', color: 'var(--muted)' }}>
            — Abhigna Naik
          </div>
        </div>
      </div>

      {/* About the project + what it isn't */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '4rem',
        marginBottom: '4rem' }}>
        <div>
          <div className="section-label">About the project</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <p style={{ fontSize: '0.9375rem', lineHeight: 1.85, color: 'var(--ink)' }}>
              SVCII cross-references S&P 500 ESG claims against publicly available satellite data —
              methane readings from ESA's Sentinel-5P, nighttime lights from NASA's VIIRS, and land
              cover from ESA's WorldCover — and produces a single score from 0 to 100.
            </p>
            <p style={{ fontSize: '0.9375rem', lineHeight: 1.85, color: 'var(--muted)' }}>
              The ESG claim text comes verbatim from real 2023 sustainability reports. The satellite
              data is independent — no company has any input into what the sensors measure. Every
              score is computed the same way for every company, with no manual adjustment.
            </p>
          </div>

          <div className="section-label" style={{ marginTop: '2rem' }}>Keep in mind</div>
          <ul style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem',
            paddingLeft: 0, listStyle: 'none' }}>
            {[
              ['Not financial advice', 'A score doesn\'t tell you whether to invest. It tells you whether the satellite data lines up with what the company claims.'],
              ['Correlation, not proof', 'High methane near a facility is a signal — not a conviction.'],
              ['Snapshot in time', 'Data covers 2021–2023. Things change.'],
              ['50 companies so far', 'Covering the S&P 500 energy, materials, utilities, and tech sectors. More coming.'],
            ].map(([title, desc]) => (
              <li key={title} style={{ display: 'flex', gap: '0.75rem' }}>
                <span style={{ color: 'var(--accent)', fontWeight: 600, flexShrink: 0 }}>—</span>
                <span style={{ fontSize: '0.875rem', color: 'var(--muted)', lineHeight: 1.7 }}>
                  <strong style={{ color: 'var(--ink)', fontWeight: 500 }}>{title}.</strong>{' '}{desc}
                </span>
              </li>
            ))}
          </ul>
        </div>

        {/* Sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div style={{ background: 'var(--paper-2)', border: '1px solid var(--paper-3)',
            borderRadius: '2px', padding: '1.25rem' }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.5625rem', fontWeight: 600,
              letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--muted)',
              marginBottom: '1rem' }}>
              Quick facts
            </div>
            {[
              ['Built in',          '2024'],
              ['Data vintage',      '2021–2023'],
              ['Companies covered', '50 S&P 500'],
              ['Cost',              'Free. Always.'],
            ].map(([label, value]) => (
              <div key={label} style={{ display: 'flex', justifyContent: 'space-between',
                padding: '0.5rem 0', borderBottom: '1px solid var(--paper-3)', gap: '1rem' }}>
                <span style={{ fontSize: '0.8125rem', color: 'var(--muted)' }}>{label}</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem',
                  color: 'var(--ink)', fontWeight: 500 }}>{value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* How to use */}
      <div style={{ marginBottom: '4rem' }}>
        <div className="section-label">How to use it</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '2px',
          background: 'var(--paper-3)', border: '1px solid var(--paper-3)',
          borderRadius: '2px', overflow: 'hidden' }}>
          {[
            ['01', 'Search a company', 'Type any S&P 500 company name or ticker into the search bar.'],
            ['02', 'Read the score', 'SVCII 0–100. Below 40 means the satellite data significantly contradicts what the company claims.'],
            ['03', 'Check the claims', 'Every score links to the actual verbatim quotes from the company\'s sustainability report.'],
          ].map(([num, title, desc]) => (
            <div key={num} style={{ background: 'var(--paper-2)', padding: '1.5rem' }}>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', fontWeight: 700,
                color: 'var(--paper-3)', lineHeight: 1, marginBottom: '0.75rem' }}>{num}</div>
              <div style={{ fontWeight: 600, fontSize: '0.875rem', marginBottom: '0.375rem' }}>{title}</div>
              <p style={{ fontSize: '0.8125rem', color: 'var(--muted)', lineHeight: 1.7 }}>{desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* CTA */}
      <div style={{ background: 'var(--accent)', borderRadius: '2px', padding: '2rem 2.5rem',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        flexWrap: 'wrap', gap: '1.5rem' }}>
        <div>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.25rem', fontWeight: 600,
            color: 'var(--paper)', marginBottom: '0.25rem' }}>
            Start checking companies.
          </div>
          <p style={{ color: 'rgba(245,242,235,0.65)', fontSize: '0.8125rem' }}>
            No account. No paywall.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <Link href="/" style={{ padding: '0.75rem 1.25rem', background: 'var(--paper)',
            color: 'var(--accent)', borderRadius: '2px', fontWeight: 600, fontSize: '0.875rem',
            textDecoration: 'none' }}>
            Search →
          </Link>
          <Link href="/explore" style={{ padding: '0.75rem 1.25rem',
            background: 'transparent', color: 'var(--paper)',
            border: '1px solid rgba(245,242,235,0.35)', borderRadius: '2px',
            fontWeight: 500, fontSize: '0.875rem', textDecoration: 'none' }}>
            Explore all data
          </Link>
        </div>
      </div>

    </div>
  );
}
