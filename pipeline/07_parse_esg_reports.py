#!/usr/bin/env python3
"""
Extract ESG claims from company sustainability report PDFs using PyMuPDF + Claude API.
Stores structured claims in esg_claims table.

Usage: python 07_parse_esg_reports.py [--db ../data/svcii.db] [--pdf path/to/report.pdf] [--ticker XOM]
"""
import sys
import json
import os
from utils import get_conn, log

DB_PATH = sys.argv[sys.argv.index("--db")     + 1] if "--db"     in sys.argv else "../data/svcii.db"
PDF_PATH = sys.argv[sys.argv.index("--pdf")   + 1] if "--pdf"    in sys.argv else None
TICKER   = sys.argv[sys.argv.index("--ticker")+ 1] if "--ticker" in sys.argv else None

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

EXTRACTION_PROMPT = """
You are an ESG analyst extracting verifiable environmental and social claims from a corporate sustainability report.

For each concrete, quantified claim you find, extract:
- claim_text: verbatim quote (max 300 chars)
- category: "environmental" | "social" | "governance"
- subcategory: "methane" | "land" | "community" | "supply_chain" | "other"
- metric_type: "absolute" (total mass/energy) | "intensity" (per unit output) | "ambiguous"
- baseline_year: integer year (null if not stated)
- target_year: integer year (null if not stated)
- magnitude_pct: percent change claimed (negative = reduction, null if not quantified)
- page_number: approximate page in source document

Return JSON array of claim objects. Only include claims with actual numbers.
Ignore aspirational language without specific targets.

Document text:
{text}
"""


def extract_text_from_pdf(pdf_path: str) -> list[tuple[int, str]]:
    """Returns list of (page_number, text) tuples."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        log.error("PyMuPDF not installed. pip install pymupdf")
        return []

    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        if text.strip():
            pages.append((i + 1, text))
    return pages


def extract_claims_with_claude(text: str) -> list[dict]:
    if not ANTHROPIC_API_KEY:
        log.error("ANTHROPIC_API_KEY not set.")
        return []

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=4096,
            messages=[
                {"role": "user", "content": EXTRACTION_PROMPT.format(text=text[:8000])}
            ],
        )
        content = msg.content[0].text
        # Extract JSON array from response
        start = content.find("[")
        end = content.rfind("]") + 1
        if start >= 0 and end > start:
            return json.loads(content[start:end])
    except Exception as e:
        log.warning(f"Claude extraction failed: {e}")
    return []


def main():
    if not PDF_PATH or not TICKER:
        log.error("Usage: python 07_parse_esg_reports.py --pdf report.pdf --ticker XOM")
        sys.exit(1)

    pages = extract_text_from_pdf(PDF_PATH)
    if not pages:
        log.error("No text extracted from PDF.")
        sys.exit(1)

    # Process in chunks of ~10 pages
    all_claims = []
    chunk_size = 10
    for i in range(0, len(pages), chunk_size):
        chunk_pages = pages[i:i + chunk_size]
        combined_text = "\n\n".join(f"[Page {p}]\n{t}" for p, t in chunk_pages)
        claims = extract_claims_with_claude(combined_text)
        all_claims.extend(claims)
        log.info(f"Pages {i+1}–{min(i+chunk_size, len(pages))}: extracted {len(claims)} claims")

    conn = get_conn(DB_PATH)
    inserted = 0
    for claim in all_claims:
        conn.execute(
            """INSERT INTO esg_claims
               (ticker, claim_text, category, subcategory, metric_type,
                baseline_year, target_year, magnitude_pct, source_doc, page_number)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                TICKER.upper(),
                claim.get("claim_text", "")[:500],
                claim.get("category", "environmental"),
                claim.get("subcategory", "other"),
                claim.get("metric_type", "ambiguous"),
                claim.get("baseline_year"),
                claim.get("target_year"),
                claim.get("magnitude_pct"),
                os.path.basename(PDF_PATH),
                claim.get("page_number"),
            ),
        )
        inserted += 1

    conn.commit()
    conn.close()
    log.info(f"Inserted {inserted} ESG claims for {TICKER} from {PDF_PATH}")


if __name__ == "__main__":
    main()
