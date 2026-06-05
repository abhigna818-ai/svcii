'use client';

interface Props {
  label: string;
  value: number;
  max?: number;
  color?: string;
  showValue?: boolean;
  suffix?: string;
}

export default function ScoreBar({
  label,
  value,
  max = 100,
  color = 'var(--accent)',
  showValue = true,
  suffix = '',
}: Props) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <span style={{ fontSize: '0.8125rem', color: 'var(--ink)' }}>{label}</span>
        {showValue && (
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--muted)' }}>
            {value.toFixed(1)}{suffix}
          </span>
        )}
      </div>
      <div
        style={{
          height: '6px',
          background: 'var(--paper-3)',
          borderRadius: '1px',
          overflow: 'hidden',
        }}
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
      >
        <div
          style={{
            height: '100%',
            width: `${pct}%`,
            background: color,
            borderRadius: '1px',
            transition: 'width 600ms ease-out',
          }}
        />
      </div>
    </div>
  );
}
