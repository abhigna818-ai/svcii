'use client';
import type { Classification } from '@/lib/types';

interface Props {
  classification: Classification;
  size?: 'sm' | 'md';
}

const MAP: Record<Classification, { label: string; color: string }> = {
  CONSISTENT:              { label: 'Consistent',          color: 'var(--signal-grn)' },
  INCONCLUSIVE:            { label: 'Inconclusive',        color: 'var(--signal-amb)' },
  'WARRANTS INVESTIGATION':{ label: 'Warrants Investigation', color: 'var(--signal-amb)' },
  'MAJOR DIVERGENCE':      { label: 'Major Divergence',    color: 'var(--signal-red)' },
};

export default function ClassificationBadge({ classification, size = 'md' }: Props) {
  const { label, color } = MAP[classification] ?? { label: classification, color: 'var(--muted)' };
  const fontSize = size === 'sm' ? '0.5625rem' : '0.625rem';

  return (
    <span
      className="badge"
      style={{ color, borderColor: color, fontSize }}
      aria-label={`Classification: ${label}`}
    >
      {label}
    </span>
  );
}
