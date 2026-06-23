'use client';
import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar,
  ResponsiveContainer, Tooltip,
} from 'recharts';

interface Props {
  eScore: number;
  sScore: number | null;
  trendDirection: number;
  magnitude: number;
  temporal: number;
  disclosure: number;
}

export default function ScoreRadarChart({
  eScore, sScore, trendDirection, magnitude, temporal, disclosure,
}: Props) {
  const data = [
    { subject: 'Trend\nDirection', value: trendDirection, max: 40 },
    { subject: 'Magnitude', value: magnitude, max: 30 },
    { subject: 'Temporal\nConsistency', value: temporal, max: 20 },
    { subject: 'Disclosure\nQuality', value: disclosure, max: 10 },
    ...(sScore != null ? [{ subject: 'Social\nScore', value: sScore, max: 100 }] : []),
  ].map(d => ({ ...d, pct: Math.round((d.value / d.max) * 100) }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <RadarChart data={data} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
        <PolarGrid stroke="var(--border)" />
        <PolarAngleAxis
          dataKey="subject"
          tick={{ fontFamily: 'IBM Plex Sans', fontSize: 9, fill: '#6B6560' }}
        />
        <Tooltip
          formatter={(val: number) => [`${val}`, '']}
          contentStyle={{
            fontFamily: 'IBM Plex Mono',
            fontSize: '0.75rem',
            background: 'var(--bg-base)',
            border: '1px solid var(--border)',
            borderRadius: '2px',
          }}
        />
        <Radar
          name="Score"
          dataKey="pct"
          stroke="var(--green-primary)"
          fill="var(--green-primary)"
          fillOpacity={0.15}
          strokeWidth={1.5}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
