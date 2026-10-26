# Validação da Fase 3 — refactor-arch

Evidências da execução da Fase 3 nos três projetos, depois da aprovação dos relatórios `audit-project-{1,2,3}.md`.

## Como a validação foi feita

1. **Baseline:** antes de alterar qualquer arquivo, `scripts/smoke_test.py` subiu cada aplicação original, executou um roteiro fixo de requisições e gravou status e corpo de cada resposta em `validation/project-N-baseline.json`.
2. **Refatoração:** transformações do playbook aplicadas somente para os achados do relatório.
3. **Testes:** suíte nova em cada projeto, cobrindo os comportamentos alterados.
4. **Pós-refatoração:** o mesmo roteiro rodou contra a aplicação refatorada (`validation/project-N-after.json`), com o log do servidor em `project-N-after.server.log`. A tabela compara status e chaves JSON de primeiro nível.

Reproduzir (na raiz do repositório):

```bash
python scripts/smoke_test.py code-smells-project reports/validation/project-1-after.json
python scripts/smoke_test.py --compare reports/validation/project-1-baseline.json reports/validation/project-1-after.json
```

O código original de cada projeto está na tag `original-projects`. Valores secretos e números de cartão que o código original expunha foram mascarados (`[REDACTED]`) nas evidências do baseline.

## Resumo

| Projeto | Boot | Testes automatizados | Smoke test (mesmo status do original) | Diferenças, todas intencionais |
|---|---|---|---|---|
| 1 — code-smells-project (Flask) | ok | 17/17 (`python -m unittest discover -s tests`) | 22/24 | `/admin/query` removido (404), `/admin/reset-db` bloqueado (403) |
| 2 — ecommerce-api-legacy (Express) | ok | 10/10 (`npm test`) | 8/9 | relatório admin sem token → 401 |
| 3 — task-manager-api (Flask) | ok | 16/16 (`python -m unittest discover -s tests`) | 29/30 | `PUT /users/2` anônimo com `role: admin` → 401 |

## Projeto 1 — code-smells-project

| Método | Rota | Antes | Depois | Chaves JSON iguais |
|---|---|---:|---:|---|
| GET | `/` | 200 | 200 | sim |
| GET | `/health` | 200 | 200 | formato alterado (ver nota) |
| GET | `/produtos` | 200 | 200 | sim |
| GET | `/produtos/1` | 200 | 200 | sim |
| GET | `/produtos/999` | 404 | 404 | sim |
| GET | `/produtos/busca?q=Mouse&categoria=informatica&preco_min=10&preco_max=500` | 200 | 200 | sim |
| POST | `/produtos` | 201 | 201 | sim |
| POST | `/produtos` | 400 | 400 | sim |
| PUT | `/produtos/1` | 200 | 200 | sim |
| DELETE | `/produtos/11` | 200 | 200 | sim |
| GET | `/usuarios` | 200 | 200 | sim |
| GET | `/usuarios/1` | 200 | 200 | sim |
| POST | `/usuarios` | 201 | 201 | sim |
| POST | `/login` | 200 | 200 | sim |
| POST | `/login` | 401 | 401 | sim |
| POST | `/pedidos` | 201 | 201 | sim |
| POST | `/pedidos` | 400 | 400 | sim |
| GET | `/pedidos` | 200 | 200 | sim |
| GET | `/pedidos/usuario/2` | 200 | 200 | sim |
| PUT | `/pedidos/1/status` | 200 | 200 | sim |
| PUT | `/pedidos/1/status` | 400 | 400 | sim |
| GET | `/relatorios/vendas` | 200 | 200 | sim |
| POST | `/admin/query` | 200 | 404 | formato alterado (ver nota) |
| POST | `/admin/reset-db` | 200 | 403 | formato alterado (ver nota) |

Notas: `/health` deixou de expor `secret_key`, `db_path` e `debug`. `GET /usuarios` e `GET /usuarios/<id>` mantêm as chaves de primeiro nível, mas o campo `senha` saiu de `dados`. As senhas passaram a ser gravadas com hash.

## Projeto 2 — ecommerce-api-legacy

| Método | Rota | Antes | Depois | Chaves JSON iguais |
|---|---|---:|---:|---|
| POST | `/api/checkout` | 200 | 200 | sim |
| POST | `/api/checkout` | 400 | 400 | sim |
| POST | `/api/checkout` | 400 | 400 | sim |
| POST | `/api/checkout` | 404 | 404 | sim |
| POST | `/api/checkout` | 400 | 400 | sim |
| GET | `/api/admin/financial-report` | 200 | 200 | sim |
| DELETE | `/api/users/1` | 200 | 200 | formato alterado (ver nota) |
| GET | `/api/admin/financial-report` | 200 | 200 | sim |
| GET | `/api/admin/financial-report` | 200 | 401 | formato alterado (ver nota) |

Notas: as rotas admin recebem `x-admin-token` no roteiro; a última linha é a mesma chamada sem token. `DELETE /api/users/:id` responde JSON `{msg}` (antes, texto) e anonimiza o usuário. O relatório financeiro devolve os mesmos valores, agora em ordem determinística (o original dependia da ordem de término dos callbacks). O log do servidor mostra só os 4 últimos dígitos do cartão; o original imprimia o cartão inteiro e a chave do gateway (`project-2-baseline.server.log`, mascarado).

Limitação: `npm audit` reporta 14 vulnerabilidades transitivas (2 low, 1 moderate, 9 high, 2 critical) na cadeia de build do `sqlite3` (`tar`, `cacache`). A correção completa exige `sqlite3@6` (breaking change), que ficou fora do escopo dos achados aprovados.

## Projeto 3 — task-manager-api

| Método | Rota | Antes | Depois | Chaves JSON iguais |
|---|---|---:|---:|---|
| GET | `/` | 200 | 200 | sim |
| GET | `/health` | 200 | 200 | sim |
| GET | `/tasks` | 200 | 200 | sim |
| GET | `/tasks/1` | 200 | 200 | sim |
| GET | `/tasks/9999` | 404 | 404 | sim |
| GET | `/tasks/search?q=a` | 200 | 200 | sim |
| GET | `/tasks/stats` | 200 | 200 | sim |
| POST | `/tasks` | 201 | 201 | sim |
| POST | `/tasks` | 400 | 400 | sim |
| PUT | `/tasks/1` | 200 | 200 | sim |
| PUT | `/tasks/1` | 400 | 400 | sim |
| GET | `/users` | 200 | 200 | sim |
| GET | `/users/1` | 200 | 200 | formato alterado (ver nota) |
| GET | `/users/9999` | 404 | 404 | sim |
| POST | `/users` | 201 | 201 | formato alterado (ver nota) |
| POST | `/users` | 400 | 400 | sim |
| GET | `/users/1/tasks` | 200 | 200 | sim |
| POST | `/login` | 200 | 200 | sim |
| POST | `/login` | 401 | 401 | sim |
| PUT | `/users/2` | 200 | 401 | formato alterado (ver nota) |
| POST | `/login` | 200 | 200 | sim |
| PUT | `/users/2` | 200 | 200 | formato alterado (ver nota) |
| GET | `/reports/summary` | 200 | 200 | sim |
| GET | `/reports/user/1` | 200 | 200 | sim |
| GET | `/categories` | 200 | 200 | sim |
| POST | `/categories` | 201 | 201 | sim |
| PUT | `/categories/1` | 200 | 200 | sim |
| DELETE | `/tasks/2` | 200 | 200 | sim |
| DELETE | `/categories/4` | 200 | 200 | sim |
| DELETE | `/users/3` | 200 | 200 | sim |

Notas: `password` saiu de todas as respostas de usuário. O roteiro faz login com a conta admin do seed (`SEED_USER_PASSWORD`) e usa o token nas rotas protegidas. O teste `test_sem_deprecation_warnings_de_utcnow_ou_query_get` confirma que as APIs deprecated deixaram de ser chamadas.

Limitação: as rotas de escrita de tasks continuam públicas, como no original; o relatório recomendava autorização apenas para usuários e categorias.
