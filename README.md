# SVCII — Satellite-Verified Corporate Impact Index

Built by **Abhigna Naik**, a 17-year-old student from India.

SVCII is a free greenwashing detection platform that cross-references S&P 500 company ESG claims against independently observable NASA and ESA satellite data. Every score is computed from public datasets and is fully reproducible. No subscription. No paywall.

Corporate sustainability reports are largely self-reported and inconsistently audited. SVCII uses atmospheric methane readings from the European Space Agency's Sentinel-5P satellite, nighttime light data from NASA's Black Marble product, and land cover from ESA's WorldCover to independently verify whether a company's claimed environmental trajectory matches what satellites actually observe.

## Methodology

**SVCII = 0.6 × E-Score + 0.4 × S-Score** (E-only if no verifiable social claims)

**E Score (0–100)** — Methane/GHG verification:
- Trend Direction Agreement (40 pts): Does satellite XCH4 trend match claimed direction?
- Magnitude Proportionality (30 pts): Is satellite change proportional to claimed magnitude?
- Temporal Consistency (20 pts): Is the trend stable across the full claim period?
- Disclosure Quality (10 pts): Absolute claim = 10 pts; intensity-based = 0 pts (−10 penalty)

**S Score (0–100)** — Community and land impact:
- Land Integrity Score: ESA WorldCover land cover change near facilities
- Community Prosperity Score: NASA VIIRS nighttime lights diff-in-diff
- Supply Chain Land Use Score: WorldCover land classification around supplier facilities
- Weighted by number of verifiable claims per category

**Classifications:** CONSISTENT (≥80) · INCONCLUSIVE (60–79) · WARRANTS INVESTIGATION (40–59) · MAJOR DIVERGENCE (<40)

## Data Sources

| Source | Use | URL |
|--------|-----|-----|
| ESA Sentinel-5P TROPOMI | Atmospheric methane (XCH4) | [GEE catalog](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_CH4) |
| EPA GHGRP | Facility-level GHG disclosures | [EPA](https://www.epa.gov/ghgreporting/ghg-reporting-program-data-sets) |
| NASA VIIRS Black Marble | Nighttime lights | [LAADS DAAC](https://ladsweb.modaps.eosdis.nasa.gov/) |
| ESA WorldCover 2020/2021 | Land cover classification | [WorldCover](https://worldcover2021.esa.int/) |
| Global Energy Monitor | Facility coordinates | [GEM Wiki](https://www.gem.wiki) |

## Run Locally

```bash
# 1. Seed the database with 50 companies of real data
cd svcii/pipeline && python 09_seed_demo_data.py

# 2. Start the API
cd ../backend && pip install -r requirements.txt && uvicorn main:app --reload

# 3. Start the frontend
cd ../frontend && npm install && npm run dev
```

Open http://localhost:3000. The API runs on http://localhost:8000.

## Deploy

**Backend → Render:**
1. Connect your GitHub repo to [render.com](https://render.com)
2. Select the `backend/` directory, use the included `render.yaml`
3. Add `CORS_ORIGINS=https://your-vercel-domain.vercel.app` in environment variables
4. Upload `data/svcii.db` to the persistent disk mounted at `/opt/render/project/src/data`

**Frontend → Vercel:**
1. Import the repo at [vercel.com](https://vercel.com)
2. Set root directory to `frontend/`
3. Add env var: `NEXT_PUBLIC_API_URL=https://svcii-api.onrender.com`

## Data Pipeline

Run scripts in order to ingest real satellite data (internet access required):

```bash
cd pipeline
python 01_fetch_companies.py          # S&P 500 company list
python 02_fetch_facilities.py         # Global Energy Monitor coordinates
python 03_fetch_epa_ghgrp.py          # EPA GHGRP methane emissions
python 04_fetch_tropomi.py            # TROPOMI XCH4 (requires GEE auth)
python 05_fetch_viirs.py              # VIIRS nighttime lights (requires NASA Earthdata)
python 06_fetch_worldcover.py         # ESA WorldCover tiles
python 07_parse_esg_reports.py --pdf report.pdf --ticker XOM  # PDF claim extraction
python 08_compute_scores.py           # Compute all SVCII scores
```

Script `09_seed_demo_data.py` populates 50 companies with curated real data and requires no external credentials.

## Limitations

- Satellite attribution is correlational, not causal
- TROPOMI resolution (5.5×3.5 km) may capture multiple sources
- ESG claims are extracted from self-reported documents
- Intensity-based claims are inherently less verifiable than absolute claims
- Data vintages: satellite data 2021–2023; ESG claims from 2023 reports

## Academic References

- Alvarez et al. (2018). Assessment of methane emissions from the U.S. oil and gas supply chain. *Science*. [doi:10.1126/science.aar7204](https://doi.org/10.1126/science.aar7204)
- Varon et al. (2021). Continuous weekly monitoring of methane emissions from the Permian Basin. *ACP*. [doi:10.5194/acp-21-7189-2021](https://doi.org/10.5194/acp-21-7189-2021)
- Jean et al. (2016). Combining satellite imagery and ML to predict poverty. *Science*. [doi:10.1126/science.aaf7894](https://doi.org/10.1126/science.aaf7894)
- Elvidge et al. (2017). VIIRS Night-Time Lights. *IJRS*. [doi:10.1080/01431161.2017.1342050](https://doi.org/10.1080/01431161.2017.1342050)

## Contributing

Pull requests welcome. Open an issue to discuss major changes. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. Focus areas: additional companies, methodology improvements, supply chain verification.

## Created by

Abhigna Naik — high school student, Bangalore, India. Built this because the data gap between what companies say and what satellites see deserved a public tool. Free for everyone, always.
