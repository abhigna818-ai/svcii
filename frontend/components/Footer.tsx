import Link from 'next/link';

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="footer-inner">
        <div>
          <strong style={{ fontFamily: 'var(--font-display)' }}>SVCII</strong>
          <span style={{ color: 'var(--muted)' }}> — Satellite-Verified Corporate Impact Index. Free, always.</span>
        </div>

        <div className="data-credits">
          <span style={{ color: 'var(--muted)', fontSize: '0.6875rem', letterSpacing: '0.05em',
            textTransform: 'uppercase', fontWeight: 500 }}>
            Satellite sources
          </span>
          <a href="https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_CH4"
            target="_blank" rel="noopener noreferrer" style={{ color: 'var(--muted)' }}>
            ESA Sentinel-5P
          </a>
          <a href="https://ladsweb.modaps.eosdis.nasa.gov/"
            target="_blank" rel="noopener noreferrer" style={{ color: 'var(--muted)' }}>
            NASA VIIRS
          </a>
          <a href="https://worldcover2021.esa.int/"
            target="_blank" rel="noopener noreferrer" style={{ color: 'var(--muted)' }}>
            ESA WorldCover
          </a>
          <a href="https://www.epa.gov/ghgreporting"
            target="_blank" rel="noopener noreferrer" style={{ color: 'var(--muted)' }}>
            EPA GHGRP
          </a>
        </div>
      </div>
    </footer>
  );
}
