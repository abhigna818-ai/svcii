'use client';
import { useState, useEffect, useCallback } from 'react';
import type { CompanyListItem } from '@/lib/types';
import { getCompanies } from '@/lib/api';
import DataTable from '@/components/DataTable';
import type { Metadata } from 'next';

const SECTORS = [
  'Energy', 'Materials', 'Industrials', 'Utilities', 'Technology',
  'Financials', 'Healthcare', 'Consumer Staples', 'Consumer Discretionary',
];

const CLASSIFICATIONS = [
  'CONSISTENT', 'INCONCLUSIVE', 'WARRANTS INVESTIGATION', 'MAJOR DIVERGENCE',
];

const METRIC_TYPES = ['absolute', 'intensity', 'ambiguous'];

function FilterSelect({
  label, value, options, onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
      <label style={{ fontSize: '0.625rem', fontWeight: 600, letterSpacing: '0.1em',
        textTransform: 'uppercase', color: 'var(--text-muted)' }}>
        {label}
      </label>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        style={{ padding: '0.5rem 0.75rem', fontFamily: 'var(--font-sans)', fontSize: '0.875rem',
          background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 'var(--radius)',
          color: 'var(--text-primary)', cursor: 'pointer' }}
      >
        <option value="">All</option>
        {options.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  );
}

export default function ExplorePage() {
  const [companies, setCompanies] = useState<CompanyListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [sector, setSector]         = useState('');
  const [classification, setClass]  = useState('');
  const [metricType, setMetric]     = useState('');
  const [minScore, setMinScore]     = useState('');
  const [maxScore, setMaxScore]     = useState('');

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getCompanies({
        sector: sector || undefined,
        classification: classification || undefined,
        metric_type: metricType || undefined,
        min_score: minScore ? parseFloat(minScore) : undefined,
        max_score: maxScore ? parseFloat(maxScore) : undefined,
      });
      setCompanies(data);
    } catch (e) {
      setError('Could not load company data. Please check that the API is running.');
    } finally {
      setLoading(false);
    }
  }, [sector, classification, metricType, minScore, maxScore]);

  useEffect(() => { fetchData(); }, [fetchData]);

  function resetFilters() {
    setSector(''); setClass(''); setMetric(''); setMinScore(''); setMaxScore('');
  }

  const hasFilters = sector || classification || metricType || minScore || maxScore;

  return (
    <div className="container" style={{ paddingTop: '2.5rem', paddingBottom: '3rem' }}>
      <h1 style={{ marginBottom: '0.5rem' }}>Explore the Dataset</h1>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.9375rem', marginBottom: '2rem' }}>
        {companies.length} compan{companies.length === 1 ? 'y' : 'ies'} · sortable by any column
      </p>

      {/* Filters */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'flex-end',
        marginBottom: '1.5rem', padding: '1.25rem', background: 'var(--bg-elevated)',
        border: 'var(--border)', borderRadius: 'var(--radius)' }}>
        <FilterSelect label="Sector" value={sector} options={SECTORS} onChange={setSector} />
        <FilterSelect label="Classification" value={classification} options={CLASSIFICATIONS} onChange={setClass} />
        <FilterSelect label="Metric type" value={metricType} options={METRIC_TYPES} onChange={setMetric} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          <label style={{ fontSize: '0.625rem', fontWeight: 600, letterSpacing: '0.1em',
            textTransform: 'uppercase', color: 'var(--text-muted)' }}>
            Score range
          </label>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <input type="number" min={0} max={100} placeholder="Min" value={minScore}
              onChange={e => setMinScore(e.target.value)}
              style={{ width: '64px', padding: '0.5rem', fontFamily: 'var(--font-mono)', fontSize: '0.875rem',
                background: 'var(--bg-base)', border: '1px solid var(--border)', borderRadius: 'var(--radius)',
                color: 'var(--text-primary)' }} />
            <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>–</span>
            <input type="number" min={0} max={100} placeholder="Max" value={maxScore}
              onChange={e => setMaxScore(e.target.value)}
              style={{ width: '64px', padding: '0.5rem', fontFamily: 'var(--font-mono)', fontSize: '0.875rem',
                background: 'var(--bg-base)', border: '1px solid var(--border)', borderRadius: 'var(--radius)',
                color: 'var(--text-primary)' }} />
          </div>
        </div>
        {hasFilters && (
          <button onClick={resetFilters} className="btn" style={{ marginTop: 'auto' }}>
            Clear filters
          </button>
        )}
      </div>

      {/* Table */}
      <div style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {[1,2,3,4,5].map(i => (
                <div key={i} className="skeleton" style={{ height: '48px' }} />
              ))}
            </div>
          </div>
        ) : error ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--red)',
            fontSize: '0.875rem' }}>
            {error}
          </div>
        ) : (
          <DataTable companies={companies} />
        )}
      </div>

      <p style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginTop: '1rem',
        fontFamily: 'var(--font-mono)' }}>
        Data vintage: 2023–2024 · Satellite sources: Sentinel-5P TROPOMI, NASA VIIRS, ESA WorldCover
      </p>
    </div>
  );
}
