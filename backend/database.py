import sqlite3
import os
from contextlib import contextmanager
from typing import Generator

DATABASE_URL = os.getenv("DATABASE_URL", "../data/svcii.db")


def get_db_path() -> str:
    return DATABASE_URL


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS companies (
                ticker TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                sector TEXT,
                industry TEXT,
                market_cap_b REAL,
                msci_esg_rating TEXT,
                sp500 INTEGER DEFAULT 1,
                has_esg_report INTEGER DEFAULT 0,
                esg_report_year INTEGER,
                facility_count INTEGER
            );

            CREATE TABLE IF NOT EXISTS svcii_scores (
                ticker TEXT PRIMARY KEY,
                svcii REAL,
                e_score REAL,
                s_score REAL,
                e_trend_direction INTEGER,
                e_magnitude_score REAL,
                e_temporal_score REAL,
                e_disclosure_score REAL,
                s_land_integrity REAL,
                s_community_prosperity REAL,
                s_supply_chain REAL,
                classification TEXT,
                metric_type TEXT,
                divergence_pct REAL,
                methodology TEXT,
                last_updated TEXT,
                data_vintage TEXT
            );

            CREATE TABLE IF NOT EXISTS esg_claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT,
                claim_text TEXT,
                category TEXT,
                subcategory TEXT,
                metric_type TEXT,
                baseline_year INTEGER,
                target_year INTEGER,
                magnitude_pct REAL,
                source_doc TEXT,
                page_number INTEGER,
                FOREIGN KEY (ticker) REFERENCES companies(ticker)
            );

            CREATE TABLE IF NOT EXISTS facilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT,
                facility_name TEXT,
                latitude REAL,
                longitude REAL,
                operation_type TEXT,
                country TEXT,
                region TEXT,
                FOREIGN KEY (ticker) REFERENCES companies(ticker)
            );

            CREATE TABLE IF NOT EXISTS satellite_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                facility_id INTEGER,
                data_type TEXT,
                period_start TEXT,
                period_end TEXT,
                value REAL,
                unit TEXT,
                source TEXT,
                FOREIGN KEY (facility_id) REFERENCES facilities(id)
            );

            CREATE INDEX IF NOT EXISTS idx_esg_claims_ticker ON esg_claims(ticker);
            CREATE INDEX IF NOT EXISTS idx_facilities_ticker ON facilities(ticker);
            CREATE INDEX IF NOT EXISTS idx_satellite_facility ON satellite_readings(facility_id);
        """)
        conn.commit()


def get_all_companies(sector: str | None = None,
                      classification: str | None = None,
                      metric_type: str | None = None,
                      min_score: float | None = None,
                      max_score: float | None = None) -> list[sqlite3.Row]:
    query = """
        SELECT c.ticker, c.name, c.sector, c.industry, c.market_cap_b, c.msci_esg_rating,
               s.svcii, s.e_score, s.s_score, s.classification, s.metric_type
        FROM companies c
        LEFT JOIN svcii_scores s ON c.ticker = s.ticker
        WHERE 1=1
    """
    params: list = []

    if sector:
        query += " AND c.sector = ?"
        params.append(sector)
    if classification:
        query += " AND s.classification = ?"
        params.append(classification)
    if metric_type:
        query += " AND s.metric_type = ?"
        params.append(metric_type)
    if min_score is not None:
        query += " AND s.svcii >= ?"
        params.append(min_score)
    if max_score is not None:
        query += " AND s.svcii <= ?"
        params.append(max_score)

    query += " ORDER BY s.svcii DESC NULLS LAST"

    with get_connection() as conn:
        return conn.execute(query, params).fetchall()


def get_company(ticker: str) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM companies WHERE ticker = ?", (ticker.upper(),)
        ).fetchone()


def get_score(ticker: str) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM svcii_scores WHERE ticker = ?", (ticker.upper(),)
        ).fetchone()


def get_claims(ticker: str) -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM esg_claims WHERE ticker = ? ORDER BY category, subcategory",
            (ticker.upper(),)
        ).fetchall()


def get_facilities(ticker: str) -> list[sqlite3.Row]:
    query = """
        SELECT f.id, f.ticker, f.facility_name, f.latitude, f.longitude,
               f.operation_type, f.country, f.region,
               xch4.value AS xch4_value,
               xch4_trend.value AS xch4_trend,
               ntl.value AS ntl_value
        FROM facilities f
        LEFT JOIN satellite_readings xch4
            ON xch4.facility_id = f.id AND xch4.data_type = 'tropomi_xch4'
            AND xch4.period_end = (
                SELECT MAX(period_end) FROM satellite_readings
                WHERE facility_id = f.id AND data_type = 'tropomi_xch4'
            )
        LEFT JOIN satellite_readings xch4_trend
            ON xch4_trend.facility_id = f.id AND xch4_trend.data_type = 'tropomi_xch4_trend'
            AND xch4_trend.period_end = (
                SELECT MAX(period_end) FROM satellite_readings
                WHERE facility_id = f.id AND data_type = 'tropomi_xch4_trend'
            )
        LEFT JOIN satellite_readings ntl
            ON ntl.facility_id = f.id AND ntl.data_type = 'viirs_ntl'
            AND ntl.period_end = (
                SELECT MAX(period_end) FROM satellite_readings
                WHERE facility_id = f.id AND data_type = 'viirs_ntl'
            )
        WHERE f.ticker = ?
    """
    with get_connection() as conn:
        return conn.execute(query, (ticker.upper(),)).fetchall()


def get_score_distribution() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT svcii FROM svcii_scores WHERE svcii IS NOT NULL"
        ).fetchall()

    buckets = [
        (0, 20, "0–20"),
        (20, 40, "20–40"),
        (40, 60, "40–60"),
        (60, 80, "60–80"),
        (80, 100, "80–100"),
    ]
    scores = [r["svcii"] for r in rows]
    result = []
    for start, end, label in buckets:
        count = sum(1 for s in scores if start <= s < end)
        if end == 100:
            count = sum(1 for s in scores if start <= s <= end)
        result.append({"bucket_start": start, "bucket_end": end, "count": count, "label": label})
    return result


def get_sector_scores() -> list[sqlite3.Row]:
    query = """
        SELECT c.sector,
               AVG(s.svcii) AS avg_svcii,
               AVG(s.e_score) AS avg_e_score,
               AVG(s.s_score) AS avg_s_score,
               COUNT(c.ticker) AS company_count,
               SUM(CASE WHEN s.classification = 'CONSISTENT' THEN 1 ELSE 0 END) AS consistent_count,
               SUM(CASE WHEN s.classification = 'MAJOR DIVERGENCE' THEN 1 ELSE 0 END) AS divergent_count
        FROM companies c
        JOIN svcii_scores s ON c.ticker = s.ticker
        WHERE c.sector IS NOT NULL AND s.svcii IS NOT NULL
        GROUP BY c.sector
        ORDER BY avg_svcii DESC
    """
    with get_connection() as conn:
        return conn.execute(query).fetchall()


def get_leaderboard(n: int = 10) -> tuple[list[sqlite3.Row], list[sqlite3.Row]]:
    with get_connection() as conn:
        top = conn.execute("""
            SELECT c.ticker, c.name, c.sector, s.svcii, s.classification
            FROM companies c JOIN svcii_scores s ON c.ticker = s.ticker
            WHERE s.svcii IS NOT NULL
            ORDER BY s.svcii DESC LIMIT ?
        """, (n,)).fetchall()
        bottom = conn.execute("""
            SELECT c.ticker, c.name, c.sector, s.svcii, s.classification
            FROM companies c JOIN svcii_scores s ON c.ticker = s.ticker
            WHERE s.svcii IS NOT NULL
            ORDER BY s.svcii ASC LIMIT ?
        """, (n,)).fetchall()
    return top, bottom


def search_companies(q: str) -> list[sqlite3.Row]:
    pattern = f"%{q}%"
    with get_connection() as conn:
        return conn.execute("""
            SELECT c.ticker, c.name, c.sector, s.svcii, s.classification
            FROM companies c
            LEFT JOIN svcii_scores s ON c.ticker = s.ticker
            WHERE c.ticker LIKE ? OR c.name LIKE ?
            ORDER BY
                CASE WHEN c.ticker = ? THEN 0
                     WHEN c.ticker LIKE ? THEN 1
                     ELSE 2 END,
                c.market_cap_b DESC NULLS LAST
            LIMIT 10
        """, (pattern, pattern, q.upper(), f"{q.upper()}%")).fetchall()


def get_stats() -> dict:
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
        scored = conn.execute(
            "SELECT COUNT(*), AVG(svcii) FROM svcii_scores WHERE svcii IS NOT NULL"
        ).fetchone()
        class_counts = conn.execute("""
            SELECT classification, COUNT(*) as cnt
            FROM svcii_scores WHERE classification IS NOT NULL
            GROUP BY classification
        """).fetchall()

    class_map = {r["classification"]: r["cnt"] for r in class_counts}
    major_div = class_map.get("MAJOR DIVERGENCE", 0)
    total_scored = scored[0] or 1

    return {
        "total_companies": total,
        "major_divergence_pct": round(major_div / total_scored * 100, 1) if total_scored else 0,
        "avg_svcii": round(scored[1] or 0, 1),
        "consistent_count": class_map.get("CONSISTENT", 0),
        "inconclusive_count": class_map.get("INCONCLUSIVE", 0),
        "warrants_investigation_count": class_map.get("WARRANTS INVESTIGATION", 0),
        "major_divergence_count": major_div,
    }
