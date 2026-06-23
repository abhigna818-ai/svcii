'use client';
import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import type { SearchResult } from '@/lib/types';
import { search } from '@/lib/api';
import ClassificationBadge from './ClassificationBadge';

export default function SearchBar() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeIdx, setActiveIdx] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const runSearch = useCallback(async (q: string) => {
    if (!q.trim()) { setResults([]); setOpen(false); return; }
    setLoading(true);
    try {
      const res = await search(q);
      setResults(res);
      setOpen(res.length > 0);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => runSearch(query), 200);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [query, runSearch]);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node) &&
          inputRef.current && !inputRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  function selectResult(ticker: string) {
    setOpen(false);
    setQuery('');
    router.push(`/company/${ticker}`);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (!open) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); setActiveIdx(i => Math.min(i + 1, results.length - 1)); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActiveIdx(i => Math.max(i - 1, -1)); }
    else if (e.key === 'Enter' && activeIdx >= 0) { selectResult(results[activeIdx].ticker); }
    else if (e.key === 'Escape') { setOpen(false); inputRef.current?.blur(); }
  }

  return (
    <div style={{ position: 'relative', width: '100%', maxWidth: '640px', margin: '0 auto' }}>
      <div style={{ position: 'relative' }}>
        <input
          ref={inputRef}
          type="search"
          value={query}
          onChange={e => { setQuery(e.target.value); setActiveIdx(-1); }}
          onFocus={(e) => { e.currentTarget.style.borderColor = 'var(--green-primary)'; results.length > 0 && setOpen(true); }}
          onBlur={(e) => { e.currentTarget.style.borderColor = 'var(--border)'; }}
          onKeyDown={handleKeyDown}
          placeholder="Search any S&P 500 company by name or ticker..."
          aria-label="Search companies"
          aria-autocomplete="list"
          aria-expanded={open}
          style={{
            width: '100%',
            padding: '0.875rem 1.25rem',
            fontFamily: 'var(--font-sans)',
            fontSize: '1rem',
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius)',
            color: 'var(--text-primary)',
            outline: 'none',
            transition: 'border-color 150ms',
          }}
        />
        {loading && (
          <span style={{ position: 'absolute', right: '1rem', top: '50%', transform: 'translateY(-50%)',
            fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Searching...
          </span>
        )}
      </div>

      {open && results.length > 0 && (
        <div
          ref={dropdownRef}
          role="listbox"
          style={{
            position: 'absolute',
            top: 'calc(100% + 4px)',
            left: 0,
            right: 0,
            background: 'var(--bg-base)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius)',
            boxShadow: '0 4px 24px rgba(0,0,0,0.12)',
            zIndex: 200,
            overflow: 'hidden',
          }}
        >
          {results.map((r, i) => (
            <button
              key={r.ticker}
              role="option"
              aria-selected={i === activeIdx}
              onClick={() => selectResult(r.ticker)}
              style={{
                display: 'flex',
                alignItems: 'center',
                width: '100%',
                padding: '0.75rem 1rem',
                background: i === activeIdx ? 'var(--bg-elevated)' : 'transparent',
                border: 'none',
                borderBottom: i < results.length - 1 ? '1px solid var(--border)' : 'none',
                cursor: 'pointer',
                textAlign: 'left',
                gap: '0.75rem',
                transition: 'background 100ms',
              }}
              onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.background = 'var(--bg-elevated)'; setActiveIdx(i); }}
              onMouseLeave={e => { if (activeIdx !== i) (e.currentTarget as HTMLButtonElement).style.background = 'transparent'; }}
            >
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem', fontWeight: 500,
                color: 'var(--green-primary)', minWidth: '3rem' }}>
                {r.ticker}
              </span>
              <span style={{ flex: 1, fontSize: '0.875rem', color: 'var(--text-primary)' }}>{r.name}</span>
              {r.sector && (
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                  {r.sector}
                </span>
              )}
              {r.classification && (
                <ClassificationBadge classification={r.classification} size="sm" />
              )}
              {r.svcii != null && (
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.875rem', fontWeight: 500,
                  minWidth: '2.5rem', textAlign: 'right' }}>
                  {r.svcii.toFixed(1)}
                </span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
