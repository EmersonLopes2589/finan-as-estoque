"""Tests for app/importer.py."""

from __future__ import annotations

import sqlite3
import textwrap

import pytest

from app.importer import _parse_amount, import_csv


SAMPLE_CSV = textwrap.dedent(
    """\
    data,descricao,valor
    2026-07-01,Salário empresa XYZ,5200.00
    2026-07-02,Aluguel apartamento,-1800.00
    2026-07-03,Supermercado Bom Preço,-342.15
    """
)


def test_import_valid_rows(memory_conn: sqlite3.Connection):
    result = import_csv(memory_conn, SAMPLE_CSV)
    assert result.total_rows == 3
    assert result.imported == 3
    assert result.duplicates == 0
    assert result.invalid_rows == []
    rows = memory_conn.execute(
        "SELECT date, description, amount, categoria FROM transactions ORDER BY date;"
    ).fetchall()
    assert len(rows) == 3
    assert rows[2]["categoria"] == "Alimentação"
    assert rows[2]["amount"] == -342.15


def test_import_dedup(memory_conn: sqlite3.Connection):
    result = import_csv(memory_conn, SAMPLE_CSV + SAMPLE_CSV)
    assert result.imported == 3
    assert result.duplicates == 3
    assert memory_conn.execute("SELECT COUNT(*) FROM transactions;").fetchone()[0] == 3


def test_import_invalid_rows_reportadas(memory_conn: sqlite3.Connection):
    csv_text = textwrap.dedent(
        """\
        data,descricao,valor
        2026-07-01,Valido,-10.00
        15/07/2026,Data invalida,-5.00
        2026-07-03,,0.00
        2026-13-99,Outro invalido,abc
        """
    )
    result = import_csv(memory_conn, csv_text)
    assert result.total_rows == 4
    assert result.imported == 1
    assert len(result.invalid_rows) == 3
    assert [r.line_number for r in result.invalid_rows] == [3, 4, 5]


def test_import_header_inválido(memory_conn: sqlite3.Connection):
    result = import_csv(memory_conn, "foo,bar,baz\n2026-07-01,x,1.0\n")
    assert result.imported == 0
    assert len(result.invalid_rows) == 1
    assert "Cabeçalho" in result.invalid_rows[0].reason


def test_import_descricao_com_vírgula(memory_conn: sqlite3.Connection):
    csv_text = textwrap.dedent(
        '''\
        data,descricao,valor
        2026-07-16,"Livraria Cultura, livros",-135.80
        '''
    )
    result = import_csv(memory_conn, csv_text)
    assert result.imported == 1
    row = memory_conn.execute(
        "SELECT description FROM transactions WHERE date='2026-07-16';"
    ).fetchone()
    assert row["description"] == "Livraria Cultura, livros"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("-342.15", -342.15),
        ("R$ 1.234,56", 1234.56),
        ("1.234,56", 1234.56),
        ("abc", None),
        ("", None),
    ],
)
def test_parse_amount(raw, expected):
    assert _parse_amount(raw) == expected


def test_import_linha_colunas_incompletas(memory_conn: sqlite3.Connection):
    """A row with fewer columns than the header never crashes the run."""
    csv_text = textwrap.dedent(
        """\
        data,descricao,valor
        bad-row
        """
    )
    result = import_csv(memory_conn, csv_text)
    assert result.total_rows == 1
    assert result.imported == 0
    assert len(result.invalid_rows) == 1
