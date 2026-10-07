"""FastAPI application: CSV import + financial summaries + inventory.

Endpoints:
  - ``GET  /``             -> index page (static/index.html)
  - ``POST /import``       -> ingest a CSV file
  - ``GET  /transacoes``   -> list transactions (filterable)
  - ``GET  /resumo``       -> totals by category and month
  - ``GET  /estoque``      -> inventory form page (static/estoque.html)
  - ``POST /estoque/itens``-> register a stock item (auto-categorized)
  - ``GET  /estoque/itens``-> list stock items
  - ``GET  /estoque/grupos`` -> totals grouped by product type
  - ``GET  /estoque.xlsx`` -> download all stock data as Excel

The database connection is provided by the :func:`get_db` dependency,
which can be overridden in tests (see ``tests/conftest.py``).
"""

from __future__ import annotations

# Ensure the project root (parent of this package) is importable when the app
# is launched directly (e.g. ``python app/main.py`` or the IDE "Run file"
# button) — otherwise ``import app.db`` raises ModuleNotFoundError.
import sys
from pathlib import Path

_ROOT = str(Path(__file__).resolve().parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import os
import sqlite3
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

import app.db as db
from app.exporter import build_inventory_workbook
from app.importer import ImportResult, import_csv
from app.inventory import categorize_product_type, validate_numeric
from app.models import (
    ImportResultOut,
    InventoryCreate,
    InventoryGroupOut,
    InventoryOut,
    ResumoOut,
    TotalPorCategoria,
    TotalPorMes,
    TransactionOut,
)

DB_PATH: Path = Path(os.getenv("FINANCAS_DB", "financas.db"))
SAMPLE_CSV_PATH: Path = Path(
    os.getenv("FINANCAS_SAMPLE_CSV", "transacoes_exemplo.csv")
)


def _seed_if_empty(
    conn: sqlite3.Connection, sample_path: Path
) -> None:
    """Seed the database with the sample CSV when no transactions exist.

    Uses ``transacoes_exemplo.csv`` (dados fictícios, conforme .clinerules)
    so the app shows a meaningful summary on first run instead of a zero
    balance.  Idempotent: skipped when the database already has data.
    """
    existing = conn.execute("SELECT COUNT(*) FROM transactions;").fetchone()[0]
    if existing:
        return
    if not sample_path.exists():
        return
    import_csv(conn, sample_path.read_text(encoding="utf-8"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = db.create_tables(DB_PATH)
    _seed_if_empty(conn, SAMPLE_CSV_PATH)
    conn.close()
    yield


app = FastAPI(title="Finanças Pessoais", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


def get_db():
    """Yield a SQLite connection for the configured database path."""
    conn = db.get_conn(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse("static/index.html")


@app.post("/import", response_model=ImportResultOut, status_code=201)
async def upload_csv(
    file: UploadFile = File(...),
    conn: sqlite3.Connection = Depends(get_db),
):
    if file is None:
        raise HTTPException(status_code=422, detail="Nenhum arquivo enviado")
    raw = (await file.read()).decode("utf-8")
    result: ImportResult = import_csv(conn, raw)
    return ImportResultOut(
        total_rows=result.total_rows,
        imported=result.imported,
        duplicates=result.duplicates,
        invalid_rows=[
            {
                "line_number": ir.line_number,
                "raw": ir.raw,
                "reason": ir.reason,
            }
            for ir in result.invalid_rows
        ],
    )


@app.get("/transacoes", response_model=list[TransactionOut])
async def list_transacoes(
    categoria: Annotated[str | None, Query()] = None,
    mes: Annotated[str | None, Query()] = None,
    conn: sqlite3.Connection = Depends(get_db),
):
    query = "SELECT * FROM transactions"
    where: list[str] = []
    params: list = []
    if categoria:
        where.append("categoria = ?")
        params.append(categoria)
    if mes:
        where.append("strftime('%Y-%m', date) = ?")
        params.append(mes)
    if where:
        query += " WHERE " + " AND ".join(where)
    query += " ORDER BY date;"
    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


@app.get("/resumo", response_model=ResumoOut)
async def resumo(
    categoria: Annotated[str | None, Query()] = None,
    mes: Annotated[str | None, Query()] = None,
    conn: sqlite3.Connection = Depends(get_db),
):
    where: list[str] = []
    params: list = []
    if categoria:
        where.append("categoria = ?")
        params.append(categoria)
    if mes:
        where.append("strftime('%Y-%m', date) = ?")
        params.append(mes)
    clause = (" WHERE " + " AND ".join(where)) if where else ""

    cat_rows = conn.execute(
        f"SELECT categoria, ROUND(SUM(amount), 2) AS total "
        f"FROM transactions{clause} GROUP BY categoria ORDER BY total DESC;",
        params,
    ).fetchall()
    mes_rows = conn.execute(
        f"SELECT strftime('%Y-%m', date) AS mes, ROUND(SUM(amount), 2) AS total "
        f"FROM transactions{clause} GROUP BY mes ORDER BY mes;",
        params,
    ).fetchall()
    saldo_row = conn.execute(
        f"SELECT ROUND(COALESCE(SUM(amount), 0), 2) AS saldo "
        f"FROM transactions{clause};",
        params,
    ).fetchone()

    return ResumoOut(
        totais_por_categoria=[
            TotalPorCategoria(categoria=r["categoria"], total=r["total"])
             for r in cat_rows
        ],
        totais_por_mes=[
            TotalPorMes(mes=r["mes"], total=r["total"]) for r in mes_rows
        ],
        saldo_total=saldo_row["saldo"],
    )


@app.get("/estoque", response_class=HTMLResponse)
async def estoque_page():
    """Serve the inventory form page."""
    return FileResponse("static/estoque.html")


@app.post("/estoque/itens", response_model=InventoryOut, status_code=201)
async def create_inventory_item(
    payload: InventoryCreate,
    conn: sqlite3.Connection = Depends(get_db),
):
    """Register a stock item with auto-categorized product type."""
    product_name = payload.product_name.strip()
    if not product_name:
        raise HTTPException(status_code=422, detail="Nome do produto é obrigatório")
    try:
        quantity = validate_numeric(payload.quantity, "quantity")
        unit_price = validate_numeric(payload.unit_price, "unit_price")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if quantity < 0 or unit_price < 0:
        raise HTTPException(status_code=422, detail="Valores devem ser >= 0")
    product_type = categorize_product_type(product_name)
    try:
        cur = conn.execute(
            "INSERT INTO inventory (product_name, product_type, quantity, unit_price) "
            "VALUES (?, ?, ?, ?);",
            (product_name, product_type, quantity, unit_price),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Item duplicado") from None
    row = conn.execute("SELECT * FROM inventory WHERE id = ?;", (cur.lastrowid,)).fetchone()
    return dict(row)


@app.get("/estoque/itens", response_model=list[InventoryOut])
async def list_inventory(
    tipo: Annotated[str | None, Query()] = None,
    conn: sqlite3.Connection = Depends(get_db),
):
    """List stock items, optionally filtered by product type."""
    query = "SELECT * FROM inventory"
    params: list = []
    if tipo:
        query += " WHERE product_type = ?"
        params.append(tipo)
    query += " ORDER BY created_at DESC, id DESC;"
    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


@app.get("/estoque/grupos", response_model=list[InventoryGroupOut])
async def inventory_groups(conn: sqlite3.Connection = Depends(get_db)):
    """Return totals grouped by product type."""
    rows = conn.execute(
        "SELECT product_type, COUNT(*) AS items, "
        "ROUND(COALESCE(SUM(quantity), 0), 2) AS total_quantity "
        "FROM inventory GROUP BY product_type ORDER BY items DESC;"
    ).fetchall()
    return [dict(r) for r in rows]


@app.get("/estoque.xlsx")
async def export_inventory_excel(conn: sqlite3.Connection = Depends(get_db)):
    """Download all inventory data as an Excel workbook (one click)."""
    items = [dict(r) for r in conn.execute("SELECT * FROM inventory ORDER BY id;").fetchall()]
    groups = [
        dict(r)
        for r in conn.execute(
            "SELECT product_type, COUNT(*) AS items, "
            "ROUND(COALESCE(SUM(quantity), 0), 2) AS total_quantity "
            "FROM inventory GROUP BY product_type ORDER BY product_type;"
        ).fetchall()
    ]
    content = build_inventory_workbook(items, groups)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="estoque.xlsx"'},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
