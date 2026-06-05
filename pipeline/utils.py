"""Shared utilities for SVCII data pipeline."""
import os
import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("svcii")

DB_PATH = os.getenv("DATABASE_URL", "../data/svcii.db")


def get_conn(db_path: str = DB_PATH) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_data_dir() -> Path:
    d = Path("../data")
    d.mkdir(parents=True, exist_ok=True)
    return d
