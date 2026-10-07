"""Tests for app/db.py schema creation."""

from __future__ import annotations

import sqlite3

import app.db as db


def test_create_tables_creates_all_tables(memory_conn: sqlite3.Connection):
    tables = {
        row["name"]
        for row in memory_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        )
    }
    assert {"transactions", "categoria_keywords"}.issubset(tables)


def test_dedup_index_exists(memory_conn: sqlite3.Connection):
    indexes = [
        row["name"]
        for row in memory_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index';"
        )
    ]
    assert "idx_transactions_dedup" in indexes


def test_default_categoria_is_outros(memory_conn: sqlite3.Connection):
    memory_conn.execute(
        "INSERT INTO transactions (date, description, amount) VALUES (?, ?, ?);",
        ("2026-07-01", "Saldo inicial", 1000.0),
    )
    memory_conn.commit()
    row = memory_conn.execute(
        "SELECT categoria FROM transactions WHERE date='2026-07-01';"
    ).fetchone()
    assert row["categoria"] == "Outros"


def test_duplicate_insert_blocked(memory_conn: sqlite3.Connection):
    sql = "INSERT INTO transactions (date, description, amount, categoria) VALUES (?, ?, ?, ?);"
    memory_conn.execute(sql, ("2026-07-01", "Teste", -10.0, "Outros"))
    memory_conn.commit()
    try:
        memory_conn.execute(sql, ("2026-07-01", "Teste", -10.0, "Outros"))
        memory_conn.commit()
    except sqlite3.IntegrityError:
        pass
    count = memory_conn.execute(
        "SELECT COUNT(*) AS c FROM transactions "
        "WHERE date='2026-07-01' AND description='Teste' AND amount=-10.0;"
    ).fetchone()["c"]
    assert count == 1
