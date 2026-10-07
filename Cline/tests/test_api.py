"""Tests for the FastAPI endpoints (app/main.py)."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.main as main


def read_sample() -> str:
    return Path("transacoes_exemplo.csv").read_text(encoding="utf-8")


def test_get_index(client: TestClient):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_import_csv_sample(client: TestClient):
    resp = client.post(
        "/import",
        files={"file": ("transacoes.csv", read_sample(), "text/csv")},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["total_rows"] > 0
    assert body["imported"] == body["total_rows"]
    assert body["duplicates"] == 0
    assert body["invalid_rows"] == []


def test_resumo_totais_por_categoria(client: TestClient):
    client.post(
        "/import",
        files={"file": ("t.csv", read_sample(), "text/csv")},
    )
    resp = client.get("/resumo")
    assert resp.status_code == 200
    data = resp.json()
    cats = {c["categoria"]: c["total"] for c in data["totais_por_categoria"]}
    assert "Alimentação" in cats
    assert "Habitação" in cats
    assert data["saldo_total"] > 0


def test_resumo_por_mes(client: TestClient):
    client.post(
        "/import",
        files={"file": ("t.csv", read_sample(), "text/csv")},
    )
    resp = client.get("/resumo?mes=2026-07")
    assert resp.status_code == 200
    data = resp.json()
    assert data["totais_por_mes"]
    assert data["totais_por_mes"][0]["mes"] == "2026-07"


def test_resumo_filtrado_por_categoria(client: TestClient):
    client.post(
        "/import",
        files={"file": ("t.csv", read_sample(), "text/csv")},
    )
    resp = client.get("/resumo?categoria=Alimentação")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["totais_por_categoria"]) == 1
    assert data["totais_por_categoria"][0]["categoria"] == "Alimentação"


def test_transacoes_list(client: TestClient):
    client.post(
        "/import",
        files={"file": ("t.csv", read_sample(), "text/csv")},
    )
    resp = client.get("/transacoes?categoria=Alimentação&mes=2026-07")
    assert resp.status_code == 200
    rows = resp.json()
    assert all(r["categoria"] == "Alimentação" for r in rows)
    assert all(r["date"].startswith("2026-07") for r in rows)


def test_import_sem_arquivo(client: TestClient):
    resp = client.post("/import")
    assert resp.status_code == 422


def test_import_linhas_invalidas_reportadas(client: TestClient):
    csv_text = textwrap.dedent(
        """\
        data,descricao,valor
        2026-01-01,Valido,-10.00
        invalida
        """
    )
    resp = client.post(
        "/import",
        files={"file": ("bad.csv", csv_text, "text/csv")},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["imported"] == 1
    assert len(body["invalid_rows"]) == 1


def test_seed_sample_data_on_startup(tmp_path: Path, monkeypatch: "pytest.MonkeyPatch"):
    """On a fresh DB, the sample CSV is imported automatically at startup."""
    db_file = tmp_path / "seed.db"
    monkeypatch.setattr(main, "DB_PATH", db_file)
    monkeypatch.setattr(main, "SAMPLE_CSV_PATH", Path("transacoes_exemplo.csv"))
    with TestClient(main.app) as c:
        # lifespan (startup) already seeded the sample CSV inside __enter__
        resp = c.get("/resumo")
        assert resp.status_code == 200
        data = resp.json()
        assert data["saldo_total"] == pytest.approx(6423.53, abs=0.01)
        total_tx = len(c.get("/transacoes").json())
        assert total_tx == 49
        assert any(
            c["categoria"] == "Receita" for c in data["totais_por_categoria"]
        )


def test_seed_is_idempotent(tmp_path: Path, monkeypatch: "pytest.MonkeyPatch"):
    """After startup seed, re-uploading the same CSV yields duplicates only."""
    db_file = tmp_path / "seed_idem.db"
    monkeypatch.setattr(main, "DB_PATH", db_file)
    monkeypatch.setattr(main, "SAMPLE_CSV_PATH", Path("transacoes_exemplo.csv"))
    with TestClient(main.app) as c:
        assert len(c.get("/transacoes").json()) == 49
        resp = c.post(
            "/import",
            files={"file": ("t.csv", read_sample(), "text/csv")},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["imported"] == 0
        assert body["duplicates"] == 49
