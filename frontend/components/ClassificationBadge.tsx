'use client';
import type { Classification } from '@/lib/types';

interface Props {
  classification: Classification;
  size?: 'sm' | 'md';
}

const MAP: Record<Classification, { label: string; cls: string }> = {
  CONSISTENT:              { label: 'Consistent',          cls: 'badge-consistent' },
  INCONCLUSIVE:            { label: 'Inconclusive',        cls: 'badge-inconclusive' },
  'WARRANTS INVESTIGATION':{ label: 'Warrants Investigation', cls: 'badge-warrants' },
  'MAJOR DIVERGENCE':      { label: 'Major Divergence',    cls: 'badge-divergence' },
};

export default function ClassificationBadge({ classification, size = 'md' }: Props) {
  const { label, cls } = MAP[classification] ?? { label: classification, cls: '' };
  const fontSize = size === 'sm' ? '0.625rem' : '0.6875rem';

  return (
    <span
      className={`badge ${cls}`}
      style={{ fontSize }}
      aria-label={`Classification: ${label}`}
    >
      {label}
    </span>
  );
}
