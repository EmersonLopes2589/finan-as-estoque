# Agentes / Instruções do Projeto

## Stack
- **Backend**: Python 3.11+ · FastAPI · SQLite (stdlib `sqlite3`)
- **Frontend**: HTML + JavaScript puro (sem bundlers)
- **Testes**: pytest

## Convenções
- Type hints obrigatórios; docstrings curtas.
- Código em inglês (variáveis/funções), mas nomes de arquivos em snake_case.
- Funções pequenas, fáceis de testar isoladamente.
- Validar entrada CSV: reportar linhas inválidas, nunca abortar a importação.
- Evitar duplicatas: `(data, descricao, valor)` como chave natural.
- Categorização padrão: "Outros" quando nenhuma keyword casar.
- Não adicionar dependências sem aviso prévio.

## Comandos
- Rodar testes: `pytest`
- Rodar servidor: `py -m uvicorn app.main:app --reload`
- Formato CSV válido: colunas `data,descricao,valor`; data em `YYYY-MM-DD`.
