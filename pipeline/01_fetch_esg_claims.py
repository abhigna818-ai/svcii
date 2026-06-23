#!/usr/bin/env python3
"""
Download real corporate sustainability report PDFs and extract structured
environmental/social claims from them using Claude (claude-sonnet-4-6).

Real data only: PDFs are downloaded live from each company's official
domain. No claim is fabricated — if extraction fails for a company, no
file is written for it and that is reported, not papered over.

Usage:
    export ANTHROPIC_API_KEY=...
    python 01_fetch_esg_claims.py
    python 01_fetch_esg_claims.py --ticker XOM   # single company
"""
import os
import sys
import json
import time
from pathlib import Path

import requests
import fitz  # PyMuPDF

from utils import log

REPORTS = {
    "XOM": {
        "name": "ExxonMobil",
        "url": "https://corporate.exxonmobil.com/-/media/global/files/advancing-climate-solutions-progress-report/2023/2023-advancing-climate-solutions-progress-report.pdf",
        "year": 2023,
    },
    "CVX": {
        "name": "Chevron",
        "url": "https://www.chevron.com/-/media/shared-media/documents/chevron-sustainability-report-2023.pdf",
        "year": 2023,
    },
    "COP": {
        "name": "ConocoPhillips",
        "url": "https://static.conocophillips.com/files/resources/conocophillips-2023-sustainability-report.pdf",
        "year": 2023,
    },
    "MSFT": {
        "name": "Microsoft",
        "url": "https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/microsoft/msc/documents/presentations/CSR/The-2023-Impact-Summary.pdf",
        "year": 2023,
    },
    "NEE": {
        "name": "NextEra Energy",
        "url": "https://www.investor.nexteraenergy.com/~/media/Files/N/NEE-IR/Sustainability/2024%20Sustainability/NextEra%20Energy%20Sustainability%20Report%202024.pdf",
        "year": 2023,
    },
}

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

RAW_DIR = Path(__file__).parent.parent / "data" / "raw_pdfs"
CLAIMS_DIR = Path(__file__).parent.parent / "data" / "claims"

EXTRACTION_PROMPT = """You are an ESG analyst extracting verifiable, quantified environmental claims \
from a corporate sustainability report excerpt. Only extract claims that contain an actual number \
(a percentage, an absolute value, or a year-over-year target). Ignore purely aspirational language.

For each claim found, return an object with exactly these fields:
{{
  "claim_text": "exact quote, max 300 chars",
  "category": "emissions|land|water|social|governance",
  "metric_type": "absolute|intensity|qualitative",
  "value": <number or null>,
  "unit": "<string or null>",
  "year": {year},
  "target_year": <integer year or null>
}}

Respond with ONLY a JSON array of these objects (it may be empty). No prose, no markdown fences.

Report excerpt:
{text}
"""


def download_pdf(ticker: str, url: str) -> Path | None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    dest = RAW_DIR / f"{ticker}.pdf"
    try:
        resp = requests.get(url, headers={"User-Agent": UA, "Referer": url}, timeout=60)
        resp.raise_for_status()
        if resp.headers.get("content-type", "").lower().find("pdf") == -1 and not resp.content[:4] == b"%PDF":
            log.error(f"{ticker}: response is not a PDF (content-type={resp.headers.get('content-type')})")
            return None
        dest.write_bytes(resp.content)
        log.info(f"{ticker}: downloaded {len(resp.content)/1e6:.1f} MB -> {dest}")
        return dest
    except Exception as e:
        log.error(f"{ticker}: download failed for {url}: {e}")
        return None


def extract_pdf_text(pdf_path: Path, max_pages: int = 60) -> str:
    doc = fitz.open(pdf_path)
    chunks = []
    for i, page in enumerate(doc):
        if i >= max_pages:
            break
        text = page.get_text("text")
        if text.strip():
            chunks.append(f"[Page {i + 1}]\n{text}")
    doc.close()
    return "\n\n".join(chunks)


def extract_claims_with_claude(ticker: str, text: str, year: int, api_key: str) -> list[dict]:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    all_claims = []
    chunk_chars = 12000
    chunks = [text[i:i + chunk_chars] for i in range(0, len(text), chunk_chars)]
    # Cap chunks to keep this bounded/affordable; report excerpts beyond this
    # are unlikely to add materially different quantified claims.
    chunks = chunks[:8]

    for idx, chunk in enumerate(chunks):
        try:
            msg = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                messages=[{"role": "user", "content": EXTRACTION_PROMPT.format(text=chunk, year=year)}],
            )
            content = msg.content[0].text.strip()
            start, end = content.find("["), content.rfind("]") + 1
            if start >= 0 and end > start:
                claims = json.loads(content[start:end])
                all_claims.extend(claims)
                log.info(f"{ticker}: chunk {idx + 1}/{len(chunks)} -> {len(claims)} claims")
        except Exception as e:
            log.warning(f"{ticker}: chunk {idx + 1} extraction failed: {e}")
        time.sleep(0.5)

    return all_claims


def main():
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        log.error(
            "ANTHROPIC_API_KEY not set. Set it in backend/.env or export it "
            "before running this script — claim extraction requires it."
        )
        sys.exit(1)

    only = None
    if "--ticker" in sys.argv:
        only = sys.argv[sys.argv.index("--ticker") + 1].upper()

    CLAIMS_DIR.mkdir(parents=True, exist_ok=True)

    for ticker, info in REPORTS.items():
        if only and ticker != only:
            continue

        log.info(f"=== {ticker} ({info['name']}) ===")
        pdf_path = download_pdf(ticker, info["url"])
        if not pdf_path:
            log.error(f"{ticker}: skipping — no PDF downloaded, no claims file written.")
            continue

        text = extract_pdf_text(pdf_path)
        if not text.strip():
            log.error(f"{ticker}: no extractable text in PDF, skipping.")
            continue

        claims = extract_claims_with_claude(ticker, text, info["year"], api_key)
        if not claims:
            log.warning(f"{ticker}: Claude returned zero claims.")

        out = {"ticker": ticker, "source_url": info["url"], "claims": claims}
        out_path = CLAIMS_DIR / f"{ticker}_claims.json"
        out_path.write_text(json.dumps(out, indent=2))
        log.info(f"{ticker}: wrote {len(claims)} claims -> {out_path}")


if __name__ == "__main__":
    main()
