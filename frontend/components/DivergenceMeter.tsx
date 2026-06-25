'use client';

interface Props {
  claimed: number;   // e.g. -20 (%)
  observed: number;  // e.g. +4  (%)
  metricType: string | null;
}

export default function DivergenceMeter({ claimed, observed, metricType }: Props) {
  const divergence = Math.abs(claimed - observed);
  const claimedPct = Math.min(100, Math.abs(claimed));
  const observedPct = Math.min(100, Math.abs(observed));

  const claimedDir = claimed < 0 ? '↓' : '↑';
  const observedDir = observed < 0 ? '↓' : observed > 0 ? '↑' : '→';
  const claimedColor = claimed < 0 ? 'var(--green-deep)' : 'var(--classification-divergence)';
  const observedColor = observed < 0 ? 'var(--green-deep)' : observed > 0 ? 'var(--classification-divergence)' : 'var(--classification-warrants)';

  return (
    <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--beige-warm)',
      borderRadius: '2px', padding: '1.25rem' }}>
      <div style={{ fontSize: '0.5625rem', fontWeight: 600, letterSpacing: '0.12em',
        textTransform: 'uppercase', color: 'var(--text-muted-light)', marginBottom: '1rem' }}>
        Claim vs. Satellite — {metricType ? metricType.toUpperCase() : 'UNKNOWN'} basis
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        {/* Claimed */}
        <div>
          <div style={{ fontSize: '0.625rem', color: 'var(--text-muted-light)', marginBottom: '0.375rem' }}>
            Claimed
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.25rem', marginBottom: '0.5rem' }}>
            <span style={{ fontFamily: 'var(--font-sans)', fontSize: '1.75rem',
              fontWeight: 700, color: claimedColor, lineHeight: 1 }}>
              {claimed > 0 ? '+' : ''}{claimed.toFixed(1)}%
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1rem', color: claimedColor }}>
              {claimedDir}
            </span>
          </div>
          <div style={{ height: '4px', background: 'var(--beige-warm)', borderRadius: '1px' }}>
            <div style={{ height: '100%', width: `${claimedPct}%`,
              background: claimedColor, borderRadius: '1px', transition: 'width 800ms ease-out' }} />
          </div>
        </div>

        {/* Observed */}
        <div>
          <div style={{ fontSize: '0.625rem', color: 'var(--text-muted-light)', marginBottom: '0.375rem' }}>
            Satellite observed
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.25rem', marginBottom: '0.5rem' }}>
            <span style={{ fontFamily: 'var(--font-sans)', fontSize: '1.75rem',
              fontWeight: 700, color: observedColor, lineHeight: 1 }}>
              {observed > 0 ? '+' : ''}{observed.toFixed(1)}%
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1rem', color: observedColor }}>
              {observedDir}
            </span>
          </div>
          <div style={{ height: '4px', background: 'var(--beige-warm)', borderRadius: '1px' }}>
            <div style={{ height: '100%', width: `${observedPct}%`,
              background: observedColor, borderRadius: '1px', transition: 'width 800ms ease-out' }} />
          </div>
        </div>
      </div>

      {/* Divergence callout */}
      <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--beige-warm)',
        display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem',
          color: divergence > 15 ? 'var(--classification-divergence)' : divergence > 8 ? 'var(--classification-warrants)' : 'var(--green-deep)',
          fontWeight: 600 }}>
          {divergence.toFixed(1)} pp divergence
        </span>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted-light)' }}>
          {divergence > 15 ? '— satellite significantly contradicts claim'
           : divergence > 8 ? '— moderate discrepancy, inconclusive'
           : '— broadly consistent'}
        </span>
      </div>
    </div>
  );
}
