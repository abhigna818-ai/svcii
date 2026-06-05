import type { Metadata } from 'next';
import '../styles/globals.css';
import 'leaflet/dist/leaflet.css';
import Nav from '@/components/Nav';
import Footer from '@/components/Footer';

export const metadata: Metadata = {
  title: {
    template: '%s | SVCII',
    default: 'SVCII — Satellite-Verified Corporate Impact Index',
  },
  description:
    'Free, open-source greenwashing detection platform. Cross-references S&P 500 ESG claims against NASA and ESA satellite data to produce independently verified impact scores.',
  keywords: ['ESG', 'greenwashing', 'satellite', 'TROPOMI', 'methane', 'S&P 500', 'sustainability'],
  openGraph: {
    title: 'SVCII — Satellite-Verified Corporate Impact Index',
    description: 'ESG claims verified by satellite. Free for retail investors.',
    type: 'website',
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>
        <Nav />
        <main>{children}</main>
        <Footer />
      </body>
    </html>
  );
}
