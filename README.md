# Finanças & Estoque

Sistema de gestão financeira pessoal com importação de CSV, resumo por categoria/mês e controle de estoque, desenvolvido em Python com FastAPI.

> Observação: o código principal do projeto está na pasta `Cline/`.

## Visão geral

Este projeto permite:

- importar transações em CSV no formato `data,descricao,valor`
- categorizar despesas e receitas automaticamente
- visualizar o saldo total e os totais por categoria e mês
- controlar itens de estoque com preços, quantidade e agrupamento por tipo
- exportar dados de estoque para Excel
- manter os dados em SQLite local

## Stack tecnológica

- Python 3.11+
- FastAPI
- SQLite
- HTML + JavaScript puro
- pytest
- openpyxl

## Estrutura do projeto

```text
finan-as-estoque/
├── README.md
├── Cline/
│   ├── AGENTS.md
│   ├── requirements.txt
│   ├── financas.db
│   ├── transacoes_exemplo.csv
│   ├── app/
│   │   ├── __init__.py
│   │   ├── categorizer.py
│   │   ├── db.py
│   │   ├── exporter.py
│   │   ├── importer.py
│   │   ├── inventory.py
│   │   ├── main.py
│   │   └── models.py
│   ├── static/
│   │   ├── index.html
│   │   ├── estoque.html
│   │   ├── app.js
│   │   ├── estoque.js
│   │   ├── estoque.css
│   │   └── index.html
│   └── tests/
│       ├── conftest.py
│       ├── test_api.py
│       ├── test_categorizer.py
│       ├── test_db.py
│       ├── test_importer.py
│       └── test_inventory.py
└──
```

## Funcionalidades

### Financeiro

- upload de arquivo CSV de transações
- validação de linhas inválidas sem interromper a importação
- deduplicação de registros repetidos
- agrupamento automático por categoria
- resumo financeiro por categoria e mês
- listagem filtrável de transações

### Estoque

- cadastro de produtos com nome, quantidade e preço
- categorização automática por tipo de produto
- agrupamento por categoria de produto
- listagem de itens com filtro por tipo
- exportação em Excel

## Requisitos

- Python 3.11+
- pip

## Como executar

1. Clone o repositório:

```bash
git clone https://github.com/EmersonLopes2589/finan-as-estoque.git
cd finan-as-estoque
```

2. Acesse a pasta do projeto:

```bash
cd Cline
```

3. Crie um ambiente virtual:

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# ou
.venv\Scripts\activate      # Windows
```

4. Instale as dependências:

```bash
pip install -r requirements.txt
```

5. Inicie a aplicação:

```bash
python -m uvicorn app.main:app --reload
```

6. Abra no navegador:

```text
http://127.0.0.1:8000
```

## Formato do CSV de transações

O sistema aceita arquivos CSV com o seguinte formato:

```csv
data,descricao,valor
2024-01-10,Salário,3500.00
2024-01-12,Supermercado,-220.50
2024-01-15,Internet,-89.90
```

Regras:

- `data` no formato `YYYY-MM-DD`
- `valor` positivo para receitas e negativo para despesas
- linhas inválidas são reportadas em vez de quebrar a importação

## Testes

Para rodar a suíte de testes:

```bash
pytest
```

## Banco de dados

O projeto usa SQLite e cria automaticamente o arquivo `financas.db` na pasta `Cline/` ao iniciar a aplicação.

## Observações

- A aplicação foi pensada para uso local e de fácil execução.
- Um arquivo de exemplo `transacoes_exemplo.csv` está disponível para testar a importação rapidamente.
- O backend usa FastAPI e a interface web é estática em `static/`, sem necessidade de bundlers ou frameworks front-end.

## Licença

Este projeto não informa uma licença específica no repositório.

## Autor

Emerson Lopes

