'use client';
import { useEffect, useState, useMemo } from 'react';
import Link from 'next/link';
import type { BlogPostListItem } from '@/lib/types';
import { getBlogPosts } from '@/lib/api';
import FadeUp from '@/components/FadeUp';

const CATEGORY_LABELS: Record<string, string> = {
  methodology: 'Methodology',
  analysis: 'Analysis',
  research: 'Research',
};

function formatDate(iso: string | null): string {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
}

function readTime(): string {
  return '5 min read';
}

export default function BlogIndexPage() {
  const [posts, setPosts] = useState<BlogPostListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [category, setCategory] = useState<string>('');

  useEffect(() => {
    getBlogPosts()
      .then(setPosts)
      .catch(() => setError('Could not load posts. Please check that the API is running.'))
      .finally(() => setLoading(false));
  }, []);

  const categories = useMemo(
    () => Array.from(new Set(posts.map(p => p.category).filter(Boolean))) as string[],
    [posts]
  );
  const filtered = category ? posts.filter(p => p.category === category) : posts;

  return (
    <div className="section section-light">
      <div className="container">
        <FadeUp>
          <h1 style={{ marginBottom: '0.75rem' }}>Research &amp; Analysis</h1>
          <p className="text-muted" style={{ maxWidth: '560px', marginBottom: '2.5rem' }}>
            Methodology explainers, company case studies, and research on the gap between
            ESG disclosure and independently observable data.
          </p>
        </FadeUp>

        {categories.length > 0 && (
          <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '2.5rem', flexWrap: 'wrap' }}>
            <button
              onClick={() => setCategory('')}
              className="btn"
              style={category === '' ? { background: 'var(--green-deep)', color: '#fff', borderColor: 'var(--green-deep)' } : {}}
            >
              All
            </button>
            {categories.map(c => (
              <button
                key={c}
                onClick={() => setCategory(c)}
                className="btn"
                style={category === c ? { background: 'var(--green-deep)', color: '#fff', borderColor: 'var(--green-deep)' } : {}}
              >
                {CATEGORY_LABELS[c] ?? c}
              </button>
            ))}
          </div>
        )}

        {loading && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1.75rem' }}>
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="skeleton" style={{ height: '220px' }} />
            ))}
          </div>
        )}

        {error && <p style={{ color: 'var(--classification-divergence)' }}>{error}</p>}

        {!loading && !error && (
          <FadeUp stagger>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1.75rem' }}>
              {filtered.map(post => (
                <Link key={post.slug} href={`/blog/${post.slug}`} style={{ textDecoration: 'none' }}>
                  <div className="card" style={{ height: '100%' }}>
                    <div className="mono text-xs" style={{ color: 'var(--green-deep)', textTransform: 'uppercase',
                      letterSpacing: '0.06em', marginBottom: '0.75rem' }}>
                      {CATEGORY_LABELS[post.category ?? ''] ?? post.category}
                    </div>
                    <h2 style={{ fontSize: '1.375rem', marginBottom: '0.75rem', lineHeight: 1.3 }}>
                      {post.title}
                    </h2>
                    <p className="text-muted" style={{ lineHeight: 1.7, marginBottom: '1.25rem' }}>
                      {post.excerpt}
                    </p>
                    <div className="text-sm text-muted" style={{ display: 'flex', gap: '0.75rem' }}>
                      <span>{formatDate(post.published_at)}</span>
                      <span>·</span>
                      <span>{readTime()}</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </FadeUp>
        )}
      </div>
    </div>
  );
}
