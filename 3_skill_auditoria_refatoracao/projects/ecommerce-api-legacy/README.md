# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
ADMIN_TOKEN=<token-de-admin> npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

### Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `ADMIN_TOKEN` | sim | Token exigido em `Authorization: Bearer <token>` nas rotas `GET /api/admin/financial-report` e `DELETE /api/users/:id`. |
| `PORT` | não | Porta HTTP (padrão `3000`). |
| `DB_FILE` | não | Arquivo SQLite (padrão `:memory:`; o schema é criado no boot, então use um arquivo novo). |
| `PAYMENT_GATEWAY_KEY` | não | Chave do gateway de pagamento (o gateway atual é simulado). |

## Testes

```bash
npm test
```

## Estrutura

```
src/
  app.js            composition root (createApp) e boot do servidor
  config/           carregamento e validação das variáveis de ambiente
  db/               wrapper sqlite3 com Promises/transações, schema e seeds
  models/           acesso a dados por tabela
  services/         casos de uso (checkout, relatório), gateway de pagamento, hash de senha
  controllers/      adaptação HTTP ↔ casos de uso e validação de entrada
  routes/           registro das rotas Express
  middlewares/      autenticação de admin e tratamento central de erros
test/               testes de API com node:test
```

Exemplos de requisições estão em `api.http`.
