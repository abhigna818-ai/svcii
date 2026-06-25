import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
import { getBlogPost, getCompany } from '@/lib/api';
import ClassificationBadge from '@/components/ClassificationBadge';
import type { BlogPost } from '@/lib/types';

interface Props {
  params: Promise<{ slug: string }>;
}

const CATEGORY_LABELS: Record<string, string> = {
  methodology: 'Methodology',
  analysis: 'Analysis',
  research: 'Research',
};

function formatDate(iso: string | null): string {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  try {
    const post = await getBlogPost(slug);
    return { title: post.title, description: post.excerpt ?? undefined };
  } catch {
    return { title: 'Post' };
  }
}

export default async function BlogPostPage({ params }: Props) {
  const { slug } = await params;
  let post: BlogPost;
  try {
    post = await getBlogPost(slug);
  } catch {
    notFound();
  }

  const company = post.ticker_mentioned
    ? await getCompany(post.ticker_mentioned).catch(() => null)
    : null;

  return (
    <article className="section section-light">
      <div className="container-narrow">
        <Link href="/blog" className="text-sm" style={{ display: 'inline-block', marginBottom: '2rem' }}>
          ← Back to Blog
        </Link>

        <div className="mono text-xs" style={{ color: 'var(--green-deep)', textTransform: 'uppercase',
          letterSpacing: '0.06em', marginBottom: '1rem', fontWeight: 600 }}>
          {CATEGORY_LABELS[post.category ?? ''] ?? post.category}
        </div>

        <h1 style={{ marginBottom: '1rem', lineHeight: 1.15 }}>{post.title}</h1>

        <div className="text-sm text-muted" style={{ display: 'flex', gap: '0.75rem', marginBottom: '2.5rem' }}>
          <span>{post.author}</span>
          <span>·</span>
          <span>{formatDate(post.published_at)}</span>
          <span>·</span>
          <span>5 min read</span>
        </div>

        {company && (
          <Link href={`/company/${company.ticker}`} style={{ textDecoration: 'none' }}>
            <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              marginBottom: '2.5rem' }}>
              <div>
                <span className="mono" style={{ fontWeight: 600 }}>{company.ticker}</span>
                <span className="text-muted text-sm" style={{ marginLeft: '0.75rem' }}>
                  Current SVCII score
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span className="mono" style={{ fontWeight: 700, fontSize: '1.25rem' }}>
                  {company.svcii?.toFixed(1) ?? '—'}
                </span>
                {company.classification && (
                  <ClassificationBadge classification={company.classification} size="sm" />
                )}
              </div>
            </div>
          </Link>
        )}

        <div className="prose" style={{ fontSize: '1.125rem', lineHeight: 1.8 }}>
          <ReactMarkdown
            components={{
              h2: (props) => <h2 style={{ marginTop: '2.5rem', marginBottom: '1rem' }} {...props} />,
              p: (props) => <p style={{ marginBottom: '1.25rem' }} {...props} />,
              blockquote: (props) => <blockquote className="pull-quote" style={{ margin: '2rem 0' }} {...props} />,
            }}
          >
            {post.content_md}
          </ReactMarkdown>
        </div>

        {company && (
          <div style={{ marginTop: '3rem', paddingTop: '2rem', borderTop: '1px solid var(--beige-warm)' }}>
            <div className="section-label">Related analysis</div>
            <Link href={`/company/${company.ticker}`} style={{ fontWeight: 600 }}>
              View full {company.ticker} score breakdown →
            </Link>
          </div>
        )}
      </div>
    </article>
  );
}
