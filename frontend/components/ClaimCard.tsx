import type { ESGClaim, SatelliteConsistency } from '@/lib/types';

interface Props {
  claim: ESGClaim;
}

function consistencyIcon(c: SatelliteConsistency | null): { symbol: string; color: string; label: string } {
  if (c === 'consistent')  return { symbol: '✓', color: 'var(--green-deep)', label: 'Satellite-consistent' };
  if (c === 'divergent')   return { symbol: '✗', color: 'var(--classification-divergence)', label: 'Satellite-divergent' };
  if (c === 'inconclusive')return { symbol: '?', color: 'var(--classification-warrants)', label: 'Inconclusive' };
  return { symbol: '·', color: 'var(--text-muted-light)', label: 'Not assessed' };
}

function metricLabel(t: string | null): string {
  if (t === 'absolute') return 'Absolute';
  if (t === 'intensity') return 'Intensity';
  if (t === 'ambiguous') return 'Ambiguous';
  return 'Unknown';
}

function metricColor(t: string | null): string {
  if (t === 'absolute') return 'var(--green-deep)';
  if (t === 'intensity') return 'var(--classification-warrants)';
  return 'var(--text-muted-light)';
}

export default function ClaimCard({ claim }: Props) {
  const { symbol, color, label } = consistencyIcon(claim.satellite_consistent);

  return (
    <div
      className="card"
      style={{ padding: '1rem 1.25rem', display: 'flex', gap: '1rem', alignItems: 'flex-start' }}
    >
      <span
        title={label}
        aria-label={label}
        style={{ fontFamily: 'var(--font-mono)', fontSize: '1rem', color, flexShrink: 0,
          marginTop: '0.125rem', fontWeight: 500 }}
      >
        {symbol}
      </span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <p style={{ fontSize: '0.875rem', lineHeight: 1.6, color: 'var(--text-dark)', marginBottom: '0.625rem',
          fontStyle: 'italic' }}>
          &ldquo;{claim.claim_text}&rdquo;
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem 1rem', alignItems: 'center' }}>
          <span
            className="badge"
            style={{ color: metricColor(claim.metric_type), borderColor: metricColor(claim.metric_type) }}
          >
            {metricLabel(claim.metric_type)}
          </span>
          {claim.baseline_year && claim.target_year && (
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted-light)' }}>
              {claim.baseline_year} → {claim.target_year}
            </span>
          )}
          {claim.magnitude_pct != null && (
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem',
              color: claim.magnitude_pct < 0 ? 'var(--green-deep)' : 'var(--classification-divergence)', fontWeight: 500 }}>
              {claim.magnitude_pct > 0 ? '+' : ''}{claim.magnitude_pct.toFixed(1)}%
            </span>
          )}
          {claim.source_doc && (
            <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted-light)' }}>
              {claim.source_doc}{claim.page_number ? ` p.${claim.page_number}` : ''}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
