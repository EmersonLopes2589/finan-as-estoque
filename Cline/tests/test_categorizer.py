"""Tests for app/categorizer.py."""

from __future__ import annotations

import pytest

from app.categorizer import DEFAULT_CATEGORY, categorizar


@pytest.mark.parametrize(
    ("descricao", "categoria"),
    [
        ("Supermercado Bom Preço", "Alimentação"),
        ("Padaria Pão Quente", "Alimentação"),
        ("iFood pedido jantar", "Alimentação"),
        ("Uber viagem centro", "Transporte"),
        ("Posto Shell combustível", "Transporte"),
        ("Aluguel apartamento", "Habitação"),
        ("Conta de luz", "Habitação"),
        ("Netflix assinatura", "Serviços"),
        ("Spotify Premium", "Serviços"),
        ("Academia SmartFit", "Serviços"),
        ("Farmácia Saúde+", "Serviços"),
        ("Freelance site cliente", "Receita"),
        ("Salário empresa XYZ", "Receita"),
        ("Estorno compra online", "Receita"),
        ("Consulta médica particular", "Serviços"),
        ("Cinema ingresso", "Lazer"),
        ("Livraria Cultura, livros", "Lazer"),
        ("Compra loja XPTO", "Compras"),
        ("Amazon compra fones", "Compras"),
        ("Transferência PIX sem descrição clara", "Outros"),
    ],
)
def test_categorizar_com_palavras_chave(descricao, categoria):
    assert categorizar(descricao) == categoria


def test_categorizar_case_insensitive():
    assert categorizar("UBER VIAGEM") == "Transporte"


def test_categorizar_fallback_default():
    assert categorizar("Transferência PIX") == DEFAULT_CATEGORY


def test_categorizar_usa_keywords_customizado():
    custom = {"Educação": ("curso", "livro")}
    assert categorizar("Curso de python", custom) == "Educação"
    assert categorizar("Aluguel", custom) == "Outros"
