'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const LINKS = [
  { href: '/explore',      label: 'Explore' },
  { href: '/methodology',  label: 'Methodology' },
  { href: '/about',        label: 'About' },
  { href: 'https://github.com/abhigna818-ai/svcii', label: 'GitHub', external: true },
];

export default function Nav() {
  const path = usePathname();
  return (
    <nav className="site-nav">
      <div className="nav-inner">
        <Link href="/" className="nav-logo">SVCII</Link>
        <ul className="nav-links">
          {LINKS.map(l => (
            <li key={l.href}>
              {l.external ? (
                <a href={l.href} target="_blank" rel="noopener noreferrer">
                  {l.label}
                </a>
              ) : (
                <Link href={l.href} className={path === l.href ? 'active' : ''}>
                  {l.label}
                </Link>
              )}
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
}
