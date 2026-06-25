'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const LINKS = [
  { href: '/explore',      label: 'Explore' },
  { href: '/blog',         label: 'Blog' },
  { href: '/methodology',  label: 'Methodology' },
  { href: '/about',        label: 'About' },
];

export default function Nav() {
  const path = usePathname();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    function onScroll() {
      setScrolled(window.scrollY > 8);
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <nav className={`site-nav${scrolled ? ' scrolled' : ''}`}>
      <div className="nav-inner">
        <Link href="/" className="nav-logo">SVCII</Link>
        <ul className="nav-links">
          {LINKS.map(l => (
            <li key={l.href}>
              <Link href={l.href} className={path === l.href || path.startsWith(l.href + '/') ? 'active' : ''}>
                {l.label}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
}
