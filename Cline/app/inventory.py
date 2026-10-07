"""Product-type categorization and numeric validation for inventory items.

Keywords are matched case-insensitively as substrings of the product
name. Anything without a match falls back to ``"Outros"``.
"""

from __future__ import annotations

from typing import Final, Mapping

PRODUCT_TYPE_KEYWORDS: Final[Mapping[str, tuple[str, ...]]] = {
    "Eletrônicos": (
        "notebook", "mouse", "teclado", "monitor", "celular", "cabo",
        "carregador", "fone", "tablet", "impressora",
    ),
    "Alimentos": (
        "arroz", "feijão", "feijao", "café", "cafe", "leite", "açúcar",
        "acucar", "farinha", "óleo", "oleo", "biscoito", "macarrão", "macarrao",
    ),
    "Limpeza": (
        "detergente", "sabão", "sabao", "álcool", "alcool", "desinfetante",
        "água sanitária", "vassoura", "rodo", "esponja",
    ),
    "Escritório": (
        "papel", "caneta", "toner", "clips", "pasta", "caderno",
        "grampeador", "envelope",
    ),
    "Ferramentas": (
        "martelo", "chave", "parafuso", "furadeira", "serra", "alicate",
        "trena",
    ),
}

DEFAULT_PRODUCT_TYPE: Final[str] = "Outros"


def categorize_product_type(product_name: str) -> str:
    """Return the product type for *product_name* (fallback ``"Outros"``)."""
    lowered = (product_name or "").lower()
    for product_type, keywords in PRODUCT_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword and keyword in lowered:
                return product_type
    return DEFAULT_PRODUCT_TYPE


def validate_numeric(value: object, field_name: str) -> float:
    """Coerce *value* to float, raising ``ValueError`` when not numeric."""
    if isinstance(value, bool):
        raise ValueError(f"{field_name} deve ser numérico")
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} deve ser numérico") from None
    return number
