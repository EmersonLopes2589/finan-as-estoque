"""SQLite connection and schema creation for the personal finance app."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Final

DEFAULT_DB_PATH: Final[Path] = Path("financas.db")

CREATE_TRANSACTIONS_SQL: Final[str] = """
CREATE TABLE IF NOT EXISTS transactions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    date         TEXT    NOT NULL,
    description  TEXT    NOT NULL,
    amount       REAL    NOT NULL,
    categoria    TEXT    NOT NULL DEFAULT 'Outros',
    imported_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

CREATE_DUPLICATE_GUARD_SQL: Final[str] = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_transactions_dedup
ON transactions (date, description, amount);
"""

CREATE_KEYWORDS_SQL: Final[str] = """
CREATE TABLE IF NOT EXISTS categoria_keywords (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword   TEXT NOT NULL,
    categoria TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_keywords_uk
ON categoria_keywords (keyword, categoria);
"""

CREATE_INVENTORY_SQL: Final[str] = """
CREATE TABLE IF NOT EXISTS inventory (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name   TEXT    NOT NULL,
    product_type   TEXT    NOT NULL DEFAULT 'Outros',
    quantity       REAL    NOT NULL CHECK (quantity >= 0),
    unit_price     REAL    NOT NULL CHECK (unit_price >= 0),
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

CREATE_INVENTORY_DEDUP_SQL: Final[str] = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_inventory_dedup
ON inventory (product_name, quantity, unit_price);
"""

SCHEMA_SQL: Final[str] = (
    CREATE_TRANSACTIONS_SQL
    + CREATE_DUPLICATE_GUARD_SQL
    + CREATE_KEYWORDS_SQL
    + CREATE_INVENTORY_SQL
    + CREATE_INVENTORY_DEDUP_SQL
)


def get_conn(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Return a SQLite connection with Row factory and foreign keys enabled."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def create_tables(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Create the application tables and return an open connection."""
    conn = get_conn(db_path)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn


if __name__ == "__main__":
    conn = create_tables()
    conn.close()
