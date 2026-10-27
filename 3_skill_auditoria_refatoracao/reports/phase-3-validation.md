# Validação da Fase 3 — refactor-arch

O código em `projects/` é a saída da execução real de `/refactor-arch`: uma sessão nova do Claude Code em cada projeto, a partir do estado original (tag `original-projects`). As saídas de cada sessão estão em `reports/runs/project-N.md`. Este documento traz a verificação independente feita depois.

## Verificação

1. **Testes criados pela skill**, rodados novamente fora das sessões.
2. **Smoke test** com `scripts/smoke_test.py`: o mesmo roteiro de requisições, com login e token onde a versão refatorada exige, roda contra o código original (`validation/project-N-baseline.json`) e contra o refatorado (`validation/project-N-after.json`). Os logs dos servidores estão nos `.server.log`. Valores secretos e cartões que o código original expunha foram mascarados no baseline.

```bash
# baseline: worktree da tag original-projects
SMOKE_PROJECTS_ROOT=<worktree>/3_skill_auditoria_refatoracao/projects python scripts/smoke_test.py code-smells-project reports/validation/project-1-baseline.json
# depois: código atual
python scripts/smoke_test.py code-smells-project reports/validation/project-1-after.json
python scripts/smoke_test.py --compare reports/validation/project-1-baseline.json reports/validation/project-1-after.json
```

## Resumo

| Projeto | Boot | Testes da skill | Endpoints com o mesmo status do original | Diferenças, todas intencionais |
|---|---|---|---|---|
| 1 — code-smells-project | ok | 30/30 | 21/25 | `/usuarios` sem token → 401; `/admin/query` e `/admin/reset-db` → 404; login do admin configurado → 200 |
| 2 — ecommerce-api-legacy | ok | 12/12 | 7/8 | relatório admin sem token → 401 |
| 3 — task-manager-api | ok | 53/53 | 28/29 | `PUT /users/2` anônimo pedindo `role: admin` → 401 |

"Chaves JSON iguais = não" com o mesmo status corresponde a remoções de dados sensíveis (`secret_key`/`db_path` do `/health`, `password` dos usuários) ou a mensagens de erro em formato novo.

## Projeto 1 — code-smells-project

| Método | Rota | Token | Antes | Depois | Chaves JSON iguais |
|---|---|---|---:|---:|---|
| GET | `/` |  | 200 | 200 | sim |
| GET | `/health` |  | 200 | 200 | não |
| POST | `/login` |  | 401 | 200 | não |
| GET | `/produtos` |  | 200 | 200 | sim |
| GET | `/produtos/1` |  | 200 | 200 | sim |
| GET | `/produtos/999` |  | 404 | 404 | sim |
| GET | `/produtos/busca?q=Mouse&categoria=informatica&preco_min=10&preco_max=500` |  | 200 | 200 | sim |
| POST | `/produtos` | sim | 201 | 201 | sim |
| POST | `/produtos` | sim | 400 | 400 | não |
| PUT | `/produtos/1` | sim | 200 | 200 | sim |
| DELETE | `/produtos/11` | sim | 200 | 200 | sim |
| GET | `/usuarios` | sim | 200 | 200 | sim |
| GET | `/usuarios/1` | sim | 200 | 200 | sim |
| POST | `/usuarios` |  | 201 | 201 | sim |
| POST | `/login` |  | 401 | 401 | sim |
| POST | `/pedidos` | sim | 201 | 201 | sim |
| POST | `/pedidos` | sim | 400 | 400 | sim |
| GET | `/pedidos` | sim | 200 | 200 | sim |
| GET | `/pedidos/usuario/1` | sim | 200 | 200 | sim |
| PUT | `/pedidos/1/status` | sim | 200 | 200 | sim |
| PUT | `/pedidos/1/status` | sim | 400 | 400 | não |
| GET | `/relatorios/vendas` | sim | 200 | 200 | sim |
| GET | `/usuarios` |  | 200 | 401 | não |
| POST | `/admin/query` |  | 200 | 404 | não |
| POST | `/admin/reset-db` |  | 200 | 404 | não |

## Projeto 2 — ecommerce-api-legacy

| Método | Rota | Token | Antes | Depois | Chaves JSON iguais |
|---|---|---|---:|---:|---|
| POST | `/api/checkout` |  | 200 | 200 | sim |
| POST | `/api/checkout` |  | 400 | 400 | sim |
| POST | `/api/checkout` |  | 404 | 404 | sim |
| POST | `/api/checkout` |  | 400 | 400 | sim |
| GET | `/api/admin/financial-report` | sim | 200 | 200 | sim |
| DELETE | `/api/users/1` | sim | 200 | 200 | sim |
| GET | `/api/admin/financial-report` | sim | 200 | 200 | sim |
| GET | `/api/admin/financial-report` |  | 200 | 401 | não |

O log do servidor refatorado só registra o boot e erros. O original imprimia o cartão inteiro e a chave do gateway a cada checkout (`project-2-baseline.server.log`, mascarado).

## Projeto 3 — task-manager-api

| Método | Rota | Token | Antes | Depois | Chaves JSON iguais |
|---|---|---|---:|---:|---|
| GET | `/` |  | 200 | 200 | sim |
| GET | `/health` |  | 200 | 200 | sim |
| POST | `/login` |  | 200 | 200 | sim |
| GET | `/tasks` |  | 200 | 200 | sim |
| GET | `/tasks/1` |  | 200 | 200 | sim |
| GET | `/tasks/9999` |  | 404 | 404 | sim |
| GET | `/tasks/search?q=a` |  | 200 | 200 | sim |
| GET | `/tasks/stats` |  | 200 | 200 | sim |
| POST | `/tasks` | sim | 201 | 201 | sim |
| POST | `/tasks` | sim | 400 | 400 | sim |
| PUT | `/tasks/1` | sim | 200 | 200 | sim |
| PUT | `/tasks/1` | sim | 400 | 400 | sim |
| GET | `/users` |  | 200 | 200 | sim |
| GET | `/users/1` |  | 200 | 200 | não |
| GET | `/users/9999` |  | 404 | 404 | sim |
| POST | `/users` |  | 201 | 201 | não |
| POST | `/users` |  | 400 | 400 | sim |
| GET | `/users/1/tasks` |  | 200 | 200 | sim |
| POST | `/login` |  | 401 | 401 | sim |
| PUT | `/users/2` |  | 200 | 401 | não |
| PUT | `/users/2` | sim | 200 | 200 | não |
| GET | `/reports/summary` |  | 200 | 200 | sim |
| GET | `/reports/user/1` |  | 200 | 200 | sim |
| GET | `/categories` |  | 200 | 200 | sim |
| POST | `/categories` | sim | 201 | 201 | sim |
| PUT | `/categories/1` | sim | 200 | 200 | sim |
| DELETE | `/tasks/2` | sim | 200 | 200 | sim |
| DELETE | `/categories/4` | sim | 200 | 200 | sim |
| DELETE | `/users/3` | sim | 200 | 200 | sim |

## Limitações registradas pela skill

- **Projeto 1:** sem limite de tentativas de login nem política de senha forte; notificações só registradas em log.
- **Projeto 2:** pagamento continua simulado; transações serializadas numa conexão SQLite única; `npm audit` não executado pela skill. A verificação manual encontrou 14 vulnerabilidades transitivas na cadeia de build do `sqlite3`; a correção completa exige `sqlite3@6` (breaking).
- **Projeto 3:** rotas `GET` continuam públicas; `NotificationService` não é usado por nenhuma rota; `marshmallow` e `requests` continuam no `requirements.txt` sem uso.
