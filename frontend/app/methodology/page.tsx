import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Methodology',
  description: 'How SVCII scores are computed from satellite data and corporate ESG claims.',
};

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section style={{ marginBottom: '3rem' }}>
      <div className="section-label">{title}</div>
      {children}
    </section>
  );
}

function CodeBlock({ children }: { children: string }) {
  return (
    <pre style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: '2px',
      padding: '1.25rem', overflowX: 'auto', fontFamily: 'var(--font-mono)', fontSize: '0.8125rem',
      lineHeight: 1.7, color: 'var(--text-primary)', marginTop: '1rem', marginBottom: '1rem' }}>
      <code>{children}</code>
    </pre>
  );
}

export default function MethodologyPage() {
  return (
    <div className="container-narrow" style={{ paddingTop: '2.5rem', paddingBottom: '4rem' }}>
      <h1 style={{ marginBottom: '0.5rem' }}>Methodology</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: '3rem', lineHeight: 1.7 }}>
        SVCII computes a single reproducible score (0–100) by comparing corporate ESG claims against
        independently observable satellite data. Two users running the same query on the same data
        vintage will always get the same result.
      </p>

      <Section title="Formula">
        <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)',
          borderRadius: '2px', padding: '1.5rem', marginBottom: '1.5rem' }}>
          <div style={{ fontFamily: 'var(--font-sans)', fontSize: '1.25rem', marginBottom: '0.5rem' }}>
            SVCII = 0.6 × E-Score + 0.4 × S-Score
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            If no verifiable social claims exist: SVCII = E-Score (E-only mode)
          </div>
        </div>
      </Section>

      <Section title="E Score — Environmental (0–100)">
        <p style={{ marginBottom: '1rem', lineHeight: 1.7 }}>
          The E score measures how well a company&apos;s methane and GHG reduction claims align with
          atmospheric satellite observations. It has four components:
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1px',
          background: 'var(--border)', marginBottom: '1.5rem', border: '1px solid var(--border)',
          borderRadius: '2px', overflow: 'hidden' }}>
          {[
            ['Trend Direction Agreement', '40 pts', 'Does the direction of satellite XCH4 change match the claimed direction? Full credit if yes, half if satellite is flat, zero if opposite.'],
            ['Magnitude Proportionality', '30 pts', 'Is the satellite-observed % change proportional to the claimed magnitude? Penalised by |claimed − observed| × 0.6.'],
            ['Temporal Consistency', '20 pts', 'Is the trend stable over the full claim period, not just the endpoints? Computed from direction-change frequency across quarterly readings.'],
            ['Disclosure Quality', '10 pts', 'Is the claim absolute (tonnes of emissions) or intensity-based (per unit output)? Absolute = 10 pts, intensity = 0 pts, with an additional −10 penalty.'],
          ].map(([name, pts, desc]) => (
            <div key={name} style={{ background: 'var(--bg-elevated)', padding: '1rem 1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
                marginBottom: '0.375rem' }}>
                <span style={{ fontWeight: 500, fontSize: '0.875rem' }}>{name}</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem',
                  color: 'var(--green-primary)', fontWeight: 500 }}>{pts}</span>
              </div>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>{desc}</p>
            </div>
          ))}
        </div>
        <CodeBlock>{`# Trend Direction Agreement (40 pts)
claimed_direction = -1 if claims.magnitude_pct < 0 else 1
trend_score = 40 if claimed == observed else (20 if observed == 0 else 0)

# Magnitude Proportionality (30 pts)
divergence = abs(claims.magnitude_pct - satellite.pct_change)
magnitude_score = max(0, 30 - divergence * 0.6)

# Temporal Consistency (20 pts)
# direction_changes / total_intervals → consistency_ratio → × 20
consistency_score = (1 - direction_changes / intervals) * 20

# Disclosure Quality (10 pts)
disclosure_score = 10 if metric_type == 'absolute' else 0
if metric_type == 'intensity': raw_score -= 10  # additional penalty`}</CodeBlock>
      </Section>

      <Section title="S Score — Social (0–100)">
        <p style={{ marginBottom: '1rem', lineHeight: 1.7 }}>
          The S score weights three satellite-derived sub-components by the number of verifiable
          claims per category. If a company makes no land claims but many community claims,
          the community component is weighted higher.
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1px',
          background: 'var(--border)', marginBottom: '1.5rem', border: '1px solid var(--border)',
          borderRadius: '2px', overflow: 'hidden' }}>
          {[
            ['Land Integrity Score (LIS)', 'ESA WorldCover', 'Fraction of natural land cover (tree, shrub, grassland, wetland) within a 25 km buffer of each facility. Computed from ESA WorldCover 2020/2021 10 m GeoTIFFs.'],
            ['Community Prosperity Score (CPS)', 'NASA VIIRS', 'Annual mean nighttime radiance (nW/cm²/sr) within facility buffer zones. Diff-in-diff vs. regional baseline normalised to 0–100. Source: NASA Black Marble VNP46A4 annual composite.'],
            ['Supply Chain Land Use Score (SLUS)', 'ESA WorldCover', 'Land cover composition (cropland vs. forest vs. urban) around supply chain facility coordinates. Penalises high conversion of natural land.'],
          ].map(([name, src, desc]) => (
            <div key={name} style={{ background: 'var(--bg-elevated)', padding: '1rem 1.25rem',
              display: 'flex', gap: '1rem' }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 500, fontSize: '0.875rem', marginBottom: '0.25rem' }}>{name}</div>
                <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>{desc}</p>
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.625rem', color: 'var(--text-muted)',
                whiteSpace: 'nowrap', marginTop: '0.25rem' }}>{src}</span>
            </div>
          ))}
        </div>
      </Section>

      <Section title="Classification">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1px',
          background: 'var(--border)', border: '1px solid var(--border)', borderRadius: '2px',
          overflow: 'hidden' }}>
          {[
            ['≥ 80', 'CONSISTENT',              'var(--green-primary)', 'Satellite data directionally consistent with ESG claims across all components.'],
            ['60–79','INCONCLUSIVE',             'var(--orange)', 'Mixed signals. Directional agreement but notable magnitude or temporal discrepancies.'],
            ['40–59','WARRANTS INVESTIGATION',   'var(--orange)', 'Notable divergence between claimed and observed trends. Warrants further scrutiny.'],
            ['< 40', 'MAJOR DIVERGENCE',         'var(--red)', 'Satellite data significantly contradicts stated ESG claims.'],
          ].map(([range, label, color, desc]) => (
            <div key={label} style={{ background: 'var(--bg-elevated)', padding: '1rem 1.25rem',
              display: 'flex', gap: '1.5rem', alignItems: 'flex-start' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)',
                minWidth: '3.5rem', marginTop: '0.25rem' }}>{range}</span>
              <span className="badge" style={{ color, borderColor: color, flexShrink: 0,
                marginTop: '0.125rem' }}>{label}</span>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', lineHeight: 1.6, margin: 0 }}>{desc}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section title="Data Sources">
        {[
          {
            name: 'Sentinel-5P TROPOMI',
            url: 'https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_CH4',
            vintage: '2021–2023',
            desc: 'ESA satellite measuring atmospheric methane column mixing ratio (XCH4) at 5.5×3.5 km ground resolution. Processed via Google Earth Engine, sampling a 25 km radius around each facility.',
          },
          {
            name: 'EPA Greenhouse Gas Reporting Program (GHGRP)',
            url: 'https://www.epa.gov/ghgreporting/ghg-reporting-program-data-sets',
            vintage: '2022',
            desc: 'Facility-level self-reported GHG data from U.S. oil and gas operations. Used to cross-check satellite-derived trends with regulatory disclosures.',
          },
          {
            name: 'NASA VIIRS Black Marble (VNP46A2/VNP46A4)',
            url: 'https://ladsweb.modaps.eosdis.nasa.gov/',
            vintage: '2020–2023',
            desc: 'Daily and annual nighttime light composites from the VIIRS Day/Night Band. Annual mean radiance (nW/cm²/sr) extracted per facility region.',
          },
          {
            name: 'ESA WorldCover 2020 + 2021',
            url: 'https://worldcover2021.esa.int/',
            vintage: '2020–2021',
            desc: '10 m global land cover classification across 11 classes. Used for land integrity scoring and supply chain land-use analysis.',
          },
          {
            name: 'Global Energy Monitor',
            url: 'https://www.gem.wiki',
            vintage: '2023',
            desc: 'Facility coordinates for S&P 500 energy sector companies. Used to geolocate extraction, refining, and power generation assets.',
          },
        ].map(s => (
          <div key={s.name} style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '1rem', marginBottom: '0.25rem' }}>
              <a href={s.url} target="_blank" rel="noopener noreferrer"
                style={{ fontWeight: 500, fontSize: '0.9375rem' }}>{s.name}</a>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.625rem',
                color: 'var(--text-muted)' }}>{s.vintage}</span>
            </div>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>{s.desc}</p>
          </div>
        ))}
      </Section>

      <Section title="Limitations">
        <ul style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', paddingLeft: '1.25rem' }}>
          {[
            'Satellite attribution is correlational, not causal. Elevated XCH4 near a facility does not prove the facility is the source — other emitters within the sensor footprint may contribute.',
            'TROPOMI resolution (5.5×3.5 km) may encompass multiple facilities or non-company sources. Urban methane plumes and agricultural emissions can overlap with industrial measurements.',
            'ESG claims are extracted from self-reported sustainability reports and may use ambiguous language, non-standard baselines, or exclude specific emission scopes (e.g. Scope 3).',
            'Intensity-based claims (per unit produced) are structurally less verifiable via satellite than absolute emission claims. SVCII penalises intensity claims to reflect this.',
            'WorldCover and VIIRS data represent the 2020–2021 and 2020–2023 periods respectively. Changes after these vintages are not captured.',
            'Only companies with publicly available ESG reports and facility coordinates are included. Data gaps may bias sector averages.',
          ].map((l, i) => (
            <li key={i} style={{ fontSize: '0.875rem', lineHeight: 1.7, color: 'var(--text-muted)' }}>{l}</li>
          ))}
        </ul>
      </Section>

      <Section title="References">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {[
            {
              cite: 'Jean, N. et al. (2016). Combining satellite imagery and machine learning to predict poverty. Science, 353(6301), 790–794.',
              doi: 'https://doi.org/10.1126/science.aaf7894',
            },
            {
              cite: 'Alvarez, R.A. et al. (2018). Assessment of methane emissions from the U.S. oil and gas supply chain. Science, 361(6398), 186–188.',
              doi: 'https://doi.org/10.1126/science.aar7204',
            },
            {
              cite: 'Varon, D.J. et al. (2021). Continuous weekly monitoring of methane emissions from the Permian Basin by inversion of TROPOMI satellite observations. Atmos. Chem. Phys., 21, 7189–7204.',
              doi: 'https://doi.org/10.5194/acp-21-7189-2021',
            },
            {
              cite: 'Elvidge, C.D. et al. (2017). VIIRS Night-Time Lights. International Journal of Remote Sensing, 38(21), 5860–5879.',
              doi: 'https://doi.org/10.1080/01431161.2017.1342050',
            },
            {
              cite: 'Zanaga, D. et al. (2022). ESA WorldCover 10 m 2021 v200. Zenodo.',
              doi: 'https://doi.org/10.5281/zenodo.7254221',
            },
          ].map(r => (
            <div key={r.doi} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)',
                flexShrink: 0, marginTop: '0.25rem' }}>—</span>
              <div>
                <p style={{ fontSize: '0.875rem', lineHeight: 1.6, marginBottom: '0.25rem' }}>{r.cite}</p>
                <a href={r.doi} target="_blank" rel="noopener noreferrer"
                  style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                  {r.doi}
                </a>
              </div>
            </div>
          ))}
        </div>
      </Section>

      <div style={{ borderTop: '1px solid var(--border)', paddingTop: '2rem' }}>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
          Questions about the methodology?{' '}
          <a href="https://github.com/svcii/svcii/issues" target="_blank" rel="noopener noreferrer">
            Open an issue on GitHub
          </a>{' '}
          or submit a pull request. SVCII is open source under the MIT License.
        </p>
      </div>
    </div>
  );
}
