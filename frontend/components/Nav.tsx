'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const LINKS = [
  { href: '/',             label: 'Search' },
  { href: '/explore',      label: 'Explore' },
  { href: '/methodology',  label: 'Methodology' },
  { href: '/about',        label: 'About' },
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
              <Link
                href={l.href}
                className={path === l.href ? 'active' : ''}
              >
                {l.label}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
}
