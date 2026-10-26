# task-manager-api

API de Task Manager em Python/Flask. O projeto já tinha camadas nominais (`models/`, `routes/`, `services/`, `utils/`); a skill `refactor-arch` completou a separação MVC e corrigiu os problemas de segurança e qualidade (relatório: `../../reports/audit-project-3.md`).

## Estrutura

```
app.py                     # composition root: create_app()
config/settings.py         # configuração por ambiente (.env opcional via python-dotenv)
database.py                # instância SQLAlchemy + PRAGMA foreign_keys no SQLite
errors.py                  # erros de aplicação (400/401/403/404/409)
models/                    # Task, User, Category: colunas, serialização, regra de atraso, hash de senha
controllers/               # casos de uso: task, user, report, category + validators
routes/                    # Blueprints HTTP finos (views): task, user, report, category, system
middlewares/               # auth (token Bearer + papéis) e error_handler central
services/                  # auth_service (token assinado), notification_service (SMTP por config)
utils/constants.py, dates.py
seed.py                    # dados de exemplo (--reset para recriar)
tests/test_api.py
```

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env        # ajuste SECRET_KEY e, se quiser, SEED_USER_PASSWORD
python seed.py
python app.py
python -m unittest discover -s tests -v
```

A aplicação sobe em `http://127.0.0.1:5000`. O `seed.py` só popula um banco vazio; use `python seed.py --reset` para recriar os dados.

## Autenticação

`POST /login` devolve `token` assinado com `SECRET_KEY` (expira em `TOKEN_MAX_AGE_SECONDS`). Envie `Authorization: Bearer <token>` para:

| Rota | Quem pode |
|---|---|
| `PUT /users/<id>` | o próprio usuário (sem mudar `role`/`active`) ou admin |
| `DELETE /users/<id>` | admin |
| `POST/PUT/DELETE /categories...` | admin ou manager |
| `POST /users` com `role` diferente de `user` | admin |

## Mudanças de contrato intencionais

- Nenhuma resposta inclui mais `password`; senhas usam hash com salt (hashes MD5 antigos são migrados no próximo login).
- O token de login deixou de ser `fake-jwt-token-<id>`; rotas de escrita de usuários/categorias exigem token.
- Entradas com tipo inválido retornam 400 (antes 500); senha mínima passou de 4 para 8 caracteres.
- Excluir categoria desvincula as tasks (`category_id = null`) em vez de deixar referências órfãs.
