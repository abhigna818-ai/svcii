'use client';
import type { Classification } from '@/lib/types';
import ClassificationBadge from './ClassificationBadge';

interface Props {
  score: number | null;
  classification: Classification | null;
  label?: string;
  size?: 'lg' | 'md' | 'sm';
}

function scoreColor(c: Classification | null): string {
  if (!c) return 'var(--text-primary)';
  if (c === 'CONSISTENT') return 'var(--green-primary)';
  if (c === 'MAJOR DIVERGENCE') return 'var(--red)';
  return 'var(--orange)';
}

export default function ScoreDisplay({ score, classification, label, size = 'lg' }: Props) {
  const fontSize = size === 'lg' ? '4.5rem' : size === 'md' ? '2.5rem' : '1.5rem';
  const color = scoreColor(classification);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', alignItems: 'flex-start' }}>
      {label && (
        <span style={{ fontFamily: 'var(--font-sans)', fontSize: '0.625rem', fontWeight: 600,
          letterSpacing: '0.15em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
          {label}
        </span>
      )}
      <span
        style={{
          fontFamily: 'var(--font-sans)',
          fontSize,
          fontWeight: 700,
          color,
          lineHeight: 1,
          letterSpacing: '-0.02em',
        }}
        aria-label={`Score: ${score ?? 'N/A'}`}
      >
        {score != null ? score.toFixed(1) : '—'}
      </span>
      {classification && <ClassificationBadge classification={classification} />}
    </div>
  );
}
