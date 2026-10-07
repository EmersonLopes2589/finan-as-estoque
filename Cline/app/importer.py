"""CSV import logic: parsing, validation, deduplication, categorization.

The importer never aborts on bad rows.  It validates each line, collects
invalid ones for reporting, skips duplicates (natural key
``date, description, amount``) and inserts the rest with a category
resolved by :func:`app.categorizer.categorizar`.
"""

from __future__ import annotations

import csv
import io
import re
from collections import namedtuple
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable

import sqlite3

from app.categorizer import categorizar

DATE_RE: re.Pattern[str] = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class InvalidRow:
    """A row that failed validation."""

    line_number: int
    raw: str
    reason: str


@dataclass
class ImportResult:
    """Aggregate outcome of an import run."""

    total_rows: int
    imported: int
    duplicates: int
    invalid_rows: list[InvalidRow] = field(default_factory=list)


def _parse_amount(raw: str) -> float | None:
    """Convert *raw* to float, tolerating ``R$`` and BR-formatted amounts.

    Tries ``float()`` first (handles ``5200.00``, ``-342.15``); on failure
    applies Brazilian conversion (``1.234,56`` → ``1234.56``).
    """
    if raw is None:
        return None
    cleaned = raw.strip().replace("R$", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        pass
    br = cleaned.replace(".", "").replace(",", ".")
    try:
        return float(br)
    except ValueError:
        return None


def _validate_row(row: dict[str, Any]) -> tuple[str, str, float] | None:
    """Return ``(date, description, amount)`` if valid, else ``None``."""
    data_raw = (row.get("data") or "").strip()
    desc_raw = (row.get("descricao") or "").strip()
    valor_raw = (row.get("valor") or "").strip()

    if not DATE_RE.match(data_raw):
        return None
    if not desc_raw:
        return None
    amount = _parse_amount(valor_raw)
    if amount is None:
        return None
    try:
        datetime.strptime(data_raw, "%Y-%m-%d")
    except ValueError:
        return None
    return data_raw, desc_raw, amount


def _insert_transaction(
    conn: sqlite3.Connection,
    date: str,
    description: str,
    amount: float,
    categoria: str,
) -> bool:
    """Insert a single transaction.  Return ``True`` if inserted."""
    try:
        conn.execute(
            "INSERT INTO transactions (date, description, amount, categoria) "
            "VALUES (?, ?, ?, ?);",
            (date, description, amount, categoria),
        )
    except sqlite3.IntegrityError:
        return False
    return True


def import_csv(conn: sqlite3.Connection, csv_text: str) -> ImportResult:
    """Parse and import *csv_text* into *conn*.

    Validation rules:
      - header must contain ``data``, ``descricao``, ``valor``;
      - ``data`` must be a valid ``YYYY-MM-DD`` date;
      - ``valor`` must be parseable as a float;
      - ``descricao`` must be non-empty.

    Invalid rows are collected and returned, never raising.
    """
    reader = csv.DictReader(io.StringIO(csv_text))
    result = ImportResult(total_rows=0, imported=0, duplicates=0)

    required = {"data", "descricao", "valor"}
    if reader.fieldnames is None or not required.issubset(
        {h.strip().lower() for h in reader.fieldnames}
    ):
        result.invalid_rows.append(
            InvalidRow(0, csv_text[:200], "Cabeçalho inválido ou inexistente")
        )
        return result

    for line_number, row in enumerate(reader, start=2):
        if row is None:
            continue
        result.total_rows += 1
        normalized = {
            (k.strip().lower() if k else k): (v.strip() if isinstance(v, str) else v)
            for k, v in row.items()
            if k is not None
        }
        validated = _validate_row(normalized)
        if validated is None:
            result.invalid_rows.append(
                InvalidRow(
                    line_number=line_number,
                    raw=",".join(f"{v}" for v in normalized.values()),
                    reason="data, descrição ou valor em formato inválido",
                )
            )
            continue
        date, description, amount = validated
        categoria = categorizar(description)
        inserted = _insert_transaction(conn, date, description, amount, categoria)
        if inserted:
            result.imported += 1
        else:
            result.duplicates += 1

    conn.commit()
    return result
