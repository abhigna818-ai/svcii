import sqlite3
import os
from contextlib import contextmanager
from typing import Generator

# Use /tmp which is ALWAYS writable on any platform
DB_PATH = "/tmp/svcii.db"


def get_db_path() -> str:
    return DB_PATH


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS companies (
                ticker TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                sector TEXT,
                market_cap_b REAL
            );
            CREATE TABLE IF NOT EXISTS svcii_scores (
                ticker TEXT PRIMARY KEY,
                e_score REAL,
                s_score REAL,
                svcii REAL,
                classification TEXT,
                FOREIGN KEY (ticker) REFERENCES companies(ticker)
            );
            CREATE TABLE IF NOT EXISTS esg_claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT,
                claim_text TEXT,
                claim_category TEXT,
                claim_type TEXT,
                FOREIGN KEY (ticker) REFERENCES companies(ticker)
            );
            CREATE TABLE IF NOT EXISTS facilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT,
                name TEXT,
                lat REAL,
                lon REAL,
                FOREIGN KEY (ticker) REFERENCES companies(ticker)
            );
            CREATE TABLE IF NOT EXISTS satellite_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT,
                metric TEXT,
                value REAL,
                year INTEGER,
                FOREIGN KEY (ticker) REFERENCES companies(ticker)
            );
        """)


def seed_if_empty() -> None:
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
        if count > 0:
            return

    companies = [
        ("XOM", "ExxonMobil", "Energy", 450.0),
        ("CVX", "Chevron", "Energy", 290.0),
        ("MSFT", "Microsoft", "Technology", 3100.0),
        ("AAPL", "Apple", "Technology", 2900.0),
        ("NEE", "NextEra Energy", "Utilities", 120.0),
        ("AMZN", "Amazon", "Consumer Discretionary", 1800.0),
        ("GOOGL", "Alphabet", "Technology", 2000.0),
        ("JPM", "JPMorgan Chase", "Financials", 550.0),
        ("JNJ", "Johnson & Johnson", "Healthcare", 380.0),
        ("PG", "Procter & Gamble", "Consumer Staples", 360.0),
        ("COP", "ConocoPhillips", "Energy", 140.0),
        ("SLB", "SLB", "Energy", 60.0),
        ("TSLA", "Tesla", "Consumer Discretionary", 800.0),
        ("META", "Meta Platforms", "Technology", 1200.0),
        ("WMT", "Walmart", "Consumer Staples", 500.0),
        ("BAC", "Bank of America", "Financials", 280.0),
        ("DUK", "Duke Energy", "Utilities", 80.0),
        ("LLY", "Eli Lilly", "Healthcare", 700.0),
        ("CAT", "Caterpillar", "Industrials", 160.0),
        ("NEM", "Newmont", "Materials", 50.0),
    ]

    scores = [
        ("XOM", 28.0, 37.0, 31.5, "MAJOR DIVERGENCE"),
        ("CVX", 30.0, 38.0, 33.2, "MAJOR DIVERGENCE"),
        ("MSFT", 91.0, 84.0, 88.2, "CONSISTENT"),
        ("AAPL", 88.0, 83.0, 86.2, "CONSISTENT"),
        ("NEE", 85.0, 80.0, 83.0, "CONSISTENT"),
        ("AMZN", 62.0, 58.0, 60.4, "INCONCLUSIVE"),
        ("GOOGL", 80.0, 75.0, 78.0, "CONSISTENT"),
        ("JPM", 55.0, 60.0, 57.0, "INCONCLUSIVE"),
        ("JNJ", 70.0, 72.0, 70.8, "INCONCLUSIVE"),
        ("PG", 72.0, 68.0, 70.4, "INCONCLUSIVE"),
        ("COP", 35.0, 40.0, 37.0, "MAJOR DIVERGENCE"),
        ("SLB", 38.0, 42.0, 39.6, "WARRANTS INVESTIGATION"),
        ("TSLA", 82.0, 78.0, 80.4, "CONSISTENT"),
        ("META", 65.0, 60.0, 63.0, "INCONCLUSIVE"),
        ("WMT", 58.0, 62.0, 59.6, "INCONCLUSIVE"),
        ("BAC", 60.0, 65.0, 62.0, "INCONCLUSIVE"),
        ("DUK", 45.0, 48.0, 46.2, "WARRANTS INVESTIGATION"),
        ("LLY", 74.0, 70.0, 72.4, "INCONCLUSIVE"),
        ("CAT", 48.0, 52.0, 49.6, "WARRANTS INVESTIGATION"),
        ("NEM", 42.0, 46.0, 43.6, "WARRANTS INVESTIGATION"),
    ]

    with get_connection() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO companies VALUES (?,?,?,?)", companies
        )
        conn.executemany(
            "INSERT OR IGNORE INTO svcii_scores VALUES (?,?,?,?,?)", scores
        )


def get_all_companies():
    with get_connection() as conn:
        return conn.execute("""
            SELECT c.ticker, c.name, c.sector, c.market_cap_b,
                   s.svcii, s.classification
            FROM companies c
            LEFT JOIN svcii_scores s ON c.ticker = s.ticker
            ORDER BY s.svcii DESC
        """).fetchall()


def get_company(ticker: str):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM companies WHERE ticker = ?", (ticker.upper(),)
        ).fetchone()


def get_score(ticker: str):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM svcii_scores WHERE ticker = ?", (ticker.upper(),)
        ).fetchone()


def get_claims(ticker: str):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM esg_claims WHERE ticker = ?", (ticker.upper(),)
        ).fetchall()


def get_facilities(ticker: str):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM facilities WHERE ticker = ?", (ticker.upper(),)
        ).fetchall()


def get_leaderboard(n: int = 10):
    with get_connection() as conn:
        top = conn.execute("""
            SELECT c.ticker, c.name, c.sector, s.svcii, s.classification
            FROM companies c JOIN svcii_scores s ON c.ticker = s.ticker
            WHERE s.svcii IS NOT NULL ORDER BY s.svcii DESC LIMIT ?
        """, (n,)).fetchall()
        bottom = conn.execute("""
            SELECT c.ticker, c.name, c.sector, s.svcii, s.classification
            FROM companies c JOIN svcii_scores s ON c.ticker = s.ticker
            WHERE s.svcii IS NOT NULL ORDER BY s.svcii ASC LIMIT ?
        """, (n,)).fetchall()
    return top, bottom


def get_sector_scores():
    with get_connection() as conn:
        return conn.execute("""
            SELECT c.sector,
                   AVG(s.svcii) as avg_svcii,
                   COUNT(c.ticker) as company_count
            FROM companies c
            JOIN svcii_scores s ON c.ticker = s.ticker
            WHERE c.sector IS NOT NULL AND s.svcii IS NOT NULL
            GROUP BY c.sector ORDER BY avg_svcii DESC
        """).fetchall()


def search_companies(q: str):
    pattern = f"%{q}%"
    with get_connection() as conn:
        return conn.execute("""
            SELECT c.ticker, c.name, c.sector, s.svcii, s.classification
            FROM companies c
            LEFT JOIN svcii_scores s ON c.ticker = s.ticker
            WHERE c.ticker LIKE ? OR c.name LIKE ?
            LIMIT 10
        """, (pattern, pattern)).fetchall()


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
    total_scored = scored[0] or 1
    major_div = class_map.get("MAJOR DIVERGENCE", 0)
    return {
        "total_companies": total,
        "avg_svcii": round(scored[1] or 0, 1),
        "major_divergence_pct": round(major_div / total_scored * 100, 1),
        "consistent_count": class_map.get("CONSISTENT", 0),
        "inconclusive_count": class_map.get("INCONCLUSIVE", 0),
        "warrants_investigation_count": class_map.get("WARRANTS INVESTIGATION", 0),
        "major_divergence_count": major_div,
    }
