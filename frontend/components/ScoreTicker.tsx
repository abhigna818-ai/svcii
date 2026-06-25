'use client';
import { useEffect, useRef } from 'react';
import type { CompanyListItem } from '@/lib/types';

type TickerCompany = Pick<CompanyListItem, 'ticker' | 'name' | 'sector' | 'svcii' | 'classification'>;

interface Props {
  companies: TickerCompany[];
}

function scoreColor(s: number | null): string {
  if (!s) return 'var(--text-muted-light)';
  if (s >= 80) return 'var(--green-deep)';
  if (s >= 60) return 'var(--classification-warrants)';
  if (s >= 40) return 'var(--classification-warrants)';
  return 'var(--classification-divergence)';
}

export default function ScoreTicker({ companies }: Props) {
  const trackRef = useRef<HTMLDivElement>(null);

  // Duplicate list for seamless loop
  const items = [...companies, ...companies].filter(c => c.svcii != null);

  return (
    <div
      style={{
        borderTop: '1px solid var(--beige-warm)',
        borderBottom: '1px solid var(--beige-warm)',
        overflow: 'hidden',
        background: 'var(--bg-surface)',
        padding: '0.5rem 0',
      }}
      aria-hidden="true"
    >
      <div
        ref={trackRef}
        style={{
          display: 'flex',
          gap: '2.5rem',
          animation: 'ticker-scroll 60s linear infinite',
          width: 'max-content',
        }}
      >
        {items.map((c, i) => (
          <a
            key={`${c.ticker}-${i}`}
            href={`/company/${c.ticker}`}
            style={{
              display: 'flex',
              alignItems: 'baseline',
              gap: '0.5rem',
              textDecoration: 'none',
              flexShrink: 0,
            }}
          >
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.6875rem',
              fontWeight: 500, color: 'var(--text-dark)', letterSpacing: '0.04em' }}>
              {c.ticker}
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.6875rem',
              color: scoreColor(c.svcii), fontWeight: 600 }}>
              {c.svcii?.toFixed(1)}
            </span>
            <span style={{ fontSize: '0.5rem', color: 'var(--beige-warm)' }}>◆</span>
          </a>
        ))}
      </div>
      <style>{`
        @keyframes ticker-scroll {
          0%   { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
      `}</style>
    </div>
  );
}
