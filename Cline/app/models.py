"""Pydantic schemas for requests and responses.

These describe the JSON contracts exposed by the FastAPI routes in
``app/main.py``.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TransactionOut(BaseModel):
    """A single stored transaction."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    date: str
    description: str
    amount: float
    categoria: str
    imported_at: str


class InvalidRowOut(BaseModel):
    """A row that failed validation during import."""

    line_number: int
    raw: str
    reason: str


class ImportResultOut(BaseModel):
    """Summary of an import run."""

    total_rows: int
    imported: int
    duplicates: int
    invalid_rows: list[InvalidRowOut]


class TotalPorCategoria(BaseModel):
    """Total amount grouped by category."""

    categoria: str
    total: float


class TotalPorMes(BaseModel):
    """Total amount grouped by month."""

    mes: str
    total: float


class ResumoOut(BaseModel):
    """Aggregate financial summary."""

    totais_por_categoria: list[TotalPorCategoria]
    totais_por_mes: list[TotalPorMes]
    saldo_total: float


class ImportRequest(BaseModel):
    """Request body for the import endpoint."""

    csv_content: str = Field(..., description="Raw CSV text of transactions")


class InventoryCreate(BaseModel):
    """Payload for registering a stock item (numbers validated)."""

    product_name: str = Field(..., min_length=1, description="Nome do produto")
    quantity: float = Field(..., ge=0, description="Quantidade em estoque")
    unit_price: float = Field(..., ge=0, description="Preço unitário")


class InventoryOut(BaseModel):
    """A stored inventory item."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_name: str
    product_type: str
    quantity: float
    unit_price: float
    created_at: str


class InventoryGroupOut(BaseModel):
    """Aggregated totals for one product type."""

    product_type: str
    items: int
    total_quantity: float
