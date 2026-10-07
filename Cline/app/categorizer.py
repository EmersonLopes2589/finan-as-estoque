"""Keyword-based transaction categorization.

The default keyword set covers the categories present in
``transacoes_exemplo.csv``.  Keywords are matched case-insensitively as
whole-word or substring occurrences within the transaction description.
Anything that does not match falls back to ``"Outros"``.
"""

from __future__ import annotations

from typing import Final, Mapping

DEFAULT_CATEGORY_KEYWORDS: Final[Mapping[str, tuple[str, ...]]] = {
    "Alimentação": (
        "supermercado",
        "padaria",
        "restaurante",
        "ifood",
        "delivery",
        "mercearia",
    ),
    "Transporte": (
        "uber",
        "cabify",
        "posto",
        "combustível",
        "gasolina",
        "ônibus",
        "metrô",
        "trem",
        "transporte",
    ),
    "Habitação": ("aluguel", "condomínio", "iptu", "internet", "água", "luz"),
    "Receita": ("salário", "saldo", "freelance", "estorno", "depósito", "renda"),
    "Serviços": (
        "netflix",
        "spotify",
        "assinatura",
        "freelance",
        "consulta",
        "médica",
        "farmácia",
        "academia",
    ),
    "Lazer": ("cinema", "livraria", "show", "evento"),
    "Compras": ("amazon", "loja", "xpto", "compra"),
    "Saúde": ("remédio", "medicamento", "hospital"),
}

DEFAULT_CATEGORY: Final[str] = "Outros"


def categorizar(
    descricao: str,
    keywords: Mapping[str, tuple[str, ...]] | None = None,
) -> str:
    """Return the category for *descricao*.

    Keywords are lower-cased and searched case-insensitively; the first
    category whose any keyword is a substring of the description wins.
    Falls back to ``"Outros"``.
    """
    mapping = keywords if keywords is not None else DEFAULT_CATEGORY_KEYWORDS
    lowered = descricao.lower()
    for categoria, kws in mapping.items():
        for kw in kws:
            if kw and kw in lowered:
                return categoria
    return DEFAULT_CATEGORY
