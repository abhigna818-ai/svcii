'use client';
import Link from 'next/link';
import type { SectorScore } from '@/lib/types';

interface Props {
  sectors: SectorScore[];
}

function scoreColor(score: number): string {
  if (score >= 80) return 'var(--signal-grn)';
  if (score >= 60) return 'var(--signal-amb)';
  if (score >= 40) return 'var(--signal-amb)';
  return 'var(--signal-red)';
}

export default function SectorGrid({ sectors }: Props) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
        gap: '1px',
        background: 'var(--paper-3)',
        border: '1px solid var(--paper-3)',
        borderRadius: 'var(--radius)',
        overflow: 'hidden',
      }}
    >
      {sectors.map(s => (
        <Link
          key={s.sector}
          href={`/explore?sector=${encodeURIComponent(s.sector)}`}
          style={{ textDecoration: 'none' }}
        >
          <div
            style={{
              background: 'var(--paper-2)',
              padding: '1.25rem',
              transition: 'background 150ms',
              cursor: 'pointer',
            }}
            onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.background = 'var(--paper-3)'; }}
            onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.background = 'var(--paper-2)'; }}
          >
            <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginBottom: '0.5rem',
              fontWeight: 500, lineHeight: 1.3 }}>
              {s.sector}
            </div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', fontWeight: 700,
              color: scoreColor(s.avg_svcii), lineHeight: 1 }}>
              {s.avg_svcii.toFixed(1)}
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.625rem', color: 'var(--muted)',
              marginTop: '0.375rem' }}>
              {s.company_count} co. · avg SVCII
            </div>
          </div>
        </Link>
      ))}
    </div>
  );
}
