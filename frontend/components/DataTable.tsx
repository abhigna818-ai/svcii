'use client';
import { useState, useMemo } from 'react';
import Link from 'next/link';
import type { CompanyListItem } from '@/lib/types';
import ClassificationBadge from './ClassificationBadge';

interface Props {
  companies: CompanyListItem[];
}

type SortKey = 'name' | 'sector' | 'svcii' | 'e_score' | 's_score' | 'msci_esg_rating';
type SortDir = 'asc' | 'desc';

function scoreCell(val: number | null) {
  if (val == null) return <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>—</span>;
  let color = 'var(--orange)';
  if (val >= 80) color = 'var(--green-primary)';
  else if (val < 40) color = 'var(--red)';
  return <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 500, color }}>{val.toFixed(1)}</span>;
}

export default function DataTable({ companies }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>('svcii');
  const [sortDir, setSortDir] = useState<SortDir>('desc');

  function handleSort(key: SortKey) {
    if (key === sortKey) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('desc'); }
  }

  const sorted = useMemo(() => {
    return [...companies].sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      const cmp = av < bv ? -1 : av > bv ? 1 : 0;
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [companies, sortKey, sortDir]);

  function SortIcon({ col }: { col: SortKey }) {
    if (col !== sortKey) return <span style={{ color: 'var(--border)' }}> ↕</span>;
    return <span> {sortDir === 'asc' ? '↑' : '↓'}</span>;
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table>
        <thead>
          <tr>
            {(
              [
                ['name',          'Company'],
                ['sector',        'Sector'],
                ['svcii',         'SVCII'],
                ['e_score',       'E Score'],
                ['s_score',       'S Score'],
                ['msci_esg_rating','MSCI'],
              ] as [SortKey, string][]
            ).map(([key, label]) => (
              <th key={key} onClick={() => handleSort(key)} aria-sort={sortKey === key ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}>
                {label}<SortIcon col={key} />
              </th>
            ))}
            <th>Classification</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map(c => (
            <tr key={c.ticker} style={{ cursor: 'pointer' }}>
              <td>
                <Link href={`/company/${c.ticker}`} style={{ textDecoration: 'none', color: 'var(--text-primary)' }}>
                  <div style={{ fontWeight: 500 }}>{c.name}</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>{c.ticker}</div>
                </Link>
              </td>
              <td style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>{c.sector ?? '—'}</td>
              <td>{scoreCell(c.svcii)}</td>
              <td>{scoreCell(c.e_score)}</td>
              <td>{c.s_score != null ? scoreCell(c.s_score) : <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>—</span>}</td>
              <td><span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem' }}>{c.msci_esg_rating ?? '—'}</span></td>
              <td>{c.classification ? <ClassificationBadge classification={c.classification} size="sm" /> : <span style={{ color: 'var(--text-muted)' }}>—</span>}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {sorted.length === 0 && (
        <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
          No companies match the selected filters.
        </div>
      )}
    </div>
  );
}
