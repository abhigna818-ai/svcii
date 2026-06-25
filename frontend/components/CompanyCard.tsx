import Link from 'next/link';
import type { CompanyListItem, LeaderboardEntry } from '@/lib/types';
import ClassificationBadge from './ClassificationBadge';

type CardData = Pick<CompanyListItem | LeaderboardEntry, 'ticker' | 'name' | 'sector' | 'svcii' | 'classification'>;

interface Props {
  company: CardData;
  rank?: number;
}

function scoreColor(score: number | null): string {
  if (score == null) return 'var(--text-muted-light)';
  if (score >= 80) return 'var(--green-deep)';
  if (score >= 60) return 'var(--classification-inconclusive)';
  if (score >= 40) return 'var(--classification-warrants)';
  return 'var(--classification-divergence)';
}

export default function CompanyCard({ company, rank }: Props) {
  return (
    <Link
      href={`/company/${company.ticker}`}
      style={{ textDecoration: 'none' }}
      aria-label={`${company.name} SVCII score: ${company.svcii ?? 'N/A'}`}
    >
      <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem', cursor: 'pointer' }}>
        {rank != null && (
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted-light)',
            minWidth: '1.5rem', textAlign: 'right' }}>
            {rank}
          </span>
        )}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontFamily: 'var(--font-sans)', fontWeight: 600, fontSize: '1rem',
            color: 'var(--text-dark)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {company.name}
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted-light)',
            marginTop: '0.125rem' }}>
            {company.ticker}
            {company.sector && <> · {company.sector}</>}
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.375rem',
          flexShrink: 0 }}>
          <span style={{ fontFamily: 'var(--font-sans)', fontSize: '1.5rem', fontWeight: 700,
            color: scoreColor(company.svcii), lineHeight: 1 }}>
            {company.svcii != null ? company.svcii.toFixed(1) : '—'}
          </span>
          {company.classification && (
            <ClassificationBadge classification={company.classification} size="sm" />
          )}
        </div>
      </div>
    </Link>
  );
}
