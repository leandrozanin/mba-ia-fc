# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express, refatorada para MVC pela skill `refactor-arch` (relatório: `../../reports/audit-project-2.md`).

## Estrutura

```
src/
├── app.js                       # composition root: createApp() + listen quando executado direto
├── config/index.js, logger.js   # configuração por ambiente e logger com níveis
├── errors.js                    # erros de aplicação (status + mensagem)
├── db/database.js, seed.js      # wrapper Promise do sqlite3, transações, schema e seed
├── models/                      # userModel, courseModel, enrollmentModel (SQL parametrizado)
├── controllers/                 # checkout, relatório, usuários + validators
├── services/                    # paymentGateway (simulado, injetável), passwordHasher (scrypt)
├── views/routes.js              # Router Express (adaptador HTTP)
└── middlewares/                 # adminAuth, errorHandler central
test/api.test.js                 # node:test
```

## Como rodar

```bash
npm install
ADMIN_API_TOKEN=um-token-forte npm start
npm test
```

A aplicação sobe em `http://localhost:3000`. O banco padrão é SQLite em memória, com seed no boot. Exemplos em `api.http`.

| Variável | Padrão | Uso |
|---|---|---|
| `PORT` | `3000` | porta HTTP |
| `DATABASE_FILE` | `:memory:` | arquivo SQLite |
| `ADMIN_API_TOKEN` | vazio (admin bloqueado, 403) | header `x-admin-token` das rotas admin |
| `PAYMENT_GATEWAY_KEY` | vazio | chave do gateway real (o simulado não usa) |
| `SEED_USER_PASSWORD` | aleatória | senha do usuário seed |
| `LOG_LEVEL` | `info` | `info`, `warn`, `error`, `silent` |

## Mudanças de contrato intencionais

- `GET /api/admin/financial-report` e `DELETE /api/users/:id` exigem `x-admin-token` (401 sem token válido).
- Checkout: novo usuário precisa de `pwd` (antes recebia senha padrão); e-mail existente exige a senha correta (401); matrícula duplicada retorna 409; payload inválido retorna 400 em vez de derrubar o processo.
- `DELETE /api/users/:id` anonimiza o usuário (preserva matrículas/pagamentos), responde JSON e retorna 404 para id inexistente.
- O relatório mantém o formato `[{course, revenue, students:[{student, paid}]}]`, agora em ordem determinística.
