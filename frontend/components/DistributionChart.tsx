'use client';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Cell, ResponsiveContainer,
} from 'recharts';
import type { ScoreDistribution } from '@/lib/types';

interface Props {
  data: ScoreDistribution[];
}

const COLORS: Record<string, string> = {
  '0–20':   '#C1121F',
  '20–40':  '#C1121F',
  '40–60':  '#E76F00',
  '60–80':  '#E76F00',
  '80–100': '#386641',
};

function CustomTooltip({ active, payload }: { active?: boolean; payload?: { payload: ScoreDistribution }[] }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div style={{
      background: 'var(--paper)',
      border: '1px solid var(--paper-3)',
      borderRadius: '2px',
      padding: '0.625rem 0.875rem',
      fontFamily: 'var(--font-mono)',
      fontSize: '0.75rem',
    }}>
      <div style={{ color: 'var(--muted)', marginBottom: '0.25rem' }}>Score {d.label}</div>
      <div style={{ color: 'var(--ink)', fontWeight: 500 }}>{d.count} companies</div>
    </div>
  );
}

export default function DistributionChart({ data }: Props) {
  return (
    <ResponsiveContainer width="100%" height={160}>
      <BarChart data={data} barCategoryGap="20%">
        <XAxis
          dataKey="label"
          tick={{ fontFamily: 'IBM Plex Mono', fontSize: 10, fill: '#6B6560' }}
          axisLine={{ stroke: '#E2DDD2' }}
          tickLine={false}
        />
        <YAxis
          tick={{ fontFamily: 'IBM Plex Mono', fontSize: 10, fill: '#6B6560' }}
          axisLine={false}
          tickLine={false}
          width={24}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'var(--paper-3)', opacity: 0.5 }} />
        <Bar dataKey="count" radius={[1, 1, 0, 0]}>
          {data.map((entry) => (
            <Cell key={entry.label} fill={COLORS[entry.label] ?? '#6B6560'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
