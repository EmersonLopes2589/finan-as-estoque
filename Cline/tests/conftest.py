"""Shared pytest fixtures using a SQLite database.

The ``client`` fixture disables the sample-CSV auto-seed so each test starts
with a clean, empty database and stays deterministic / hermetic.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

import app.db as db
import app.main as main


@pytest.fixture
def conn(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    """Yield a connection to a fresh temp-file DB schema (auto-closed)."""
    db.create_tables(tmp_path / "test.db")
    yield db.get_conn(tmp_path / "test.db")


@pytest.fixture
def memory_conn() -> Iterator[sqlite3.Connection]:
    """Yield a connection to an in-memory SQLite schema (auto-closed)."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(db.SCHEMA_SQL)
    yield conn
    conn.close()


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Yield a TestClient backed by a fresh, seeded-free database.

    Seeding of ``transacoes_exemplo.csv`` is disabled by pointing
    ``SAMPLE_CSV_PATH`` at a non-existent file, keeping the DB empty unless a
    test explicitly enables it.
    """
    db_file = tmp_path / "api_test.db"
    monkeypatch.setattr(main, "DB_PATH", db_file)
    monkeypatch.setattr(main, "SAMPLE_CSV_PATH", tmp_path / "missing.csv")
    with TestClient(main.app) as c:
        yield c
