# code-smells-project

API de E-commerce em Python/Flask, refatorada para MVC pela skill `refactor-arch` (relatório: `../../reports/audit-project-1.md`).

## Estrutura

```
app.py                      # composition root: create_app() + execução
config/settings.py          # configuração lida do ambiente
errors.py                   # exceções de aplicação (400/401/403/404/409)
models/                     # acesso a dados (SQL parametrizado)
  database.py               #   conexão por request, schema, seed, migração de senhas
  produto_model.py, usuario_model.py, pedido_model.py
controllers/                # casos de uso e regras de negócio
  validators.py             #   validação compartilhada
  produto_controller.py, usuario_controller.py, pedido_controller.py,
  relatorio_controller.py, sistema_controller.py
views/routes.py             # Blueprint HTTP (request/response)
middlewares/error_handler.py# tratamento de erros centralizado
services/notification_service.py
tests/test_api.py
```

## Como rodar

```bash
pip install -r requirements.txt
export SECRET_KEY=...   # variáveis disponíveis em .env.example
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000`. O banco SQLite (`DATABASE_PATH`, padrão `loja.db`) é criado no boot com produtos e usuários de exemplo.

| Variável | Padrão | Uso |
|---|---|---|
| `SECRET_KEY` | aleatória por processo | chave do Flask; defina em produção |
| `DATABASE_PATH` | `loja.db` | arquivo SQLite |
| `DEBUG` / `HOST` / `PORT` | `false` / `127.0.0.1` / `5000` | servidor |
| `CORS_ORIGINS` | vazio (CORS desligado) | origens separadas por vírgula |
| `SEED_DEMO_DATA` | `true` | cria dados de exemplo em banco vazio |
| `SEED_USER_PASSWORD` | aleatória | senha das contas de exemplo |
| `ALLOW_DB_RESET` | `false` | habilita `POST /admin/reset-db` |

## Testes

```bash
python -m unittest discover -s tests -v
```

## Mudanças de contrato intencionais

- `GET /usuarios` e `GET /usuarios/<id>` não retornam mais `senha`; senhas são gravadas com hash.
- `GET /health` não expõe `secret_key`, `db_path` nem `debug`.
- `POST /admin/query` foi removido (404); `POST /admin/reset-db` retorna 403 salvo `ALLOW_DB_RESET=true`.
- Entradas inválidas retornam 400 (antes 500); e-mail duplicado retorna 409; status de pedido inexistente retorna 404.
- Cancelar um pedido devolve o estoque; pedido cancelado não muda mais de status (409).
