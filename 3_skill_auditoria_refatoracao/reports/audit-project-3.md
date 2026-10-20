# Relatorio de Auditoria — Projeto 3: task-manager-api

## Analise do projeto
- Linguagem/framework: Python 3.12 / Flask 3.0.0 e Flask-SQLAlchemy 3.1.1.
- Banco: SQLite via SQLAlchemy.
- Dominio: gerenciamento de tarefas, usuarios, categorias e relatorios.
- Arquitetura: existem diretorios `models`, `routes`, `services` e `utils`, mas handlers ainda executam validacao, consultas e calculos extensos.
- Arquivos-fonte analisados: 15 arquivos Python.
- Baseline: 11 rotas GET representativas responderam; colecoes/health deram 200 e IDs inexistentes deram 404 como esperado.

## Resumo
| Severidade | Quantidade |
|---|---:|
| CRITICAL | 1 |
| HIGH | 1 |
| MEDIUM | 2 |
| LOW | 2 |
| **Total** | **6** |

## Achados

### [CRITICAL] Chaves e credenciais SMTP hardcoded
- **Local:** `app.py:13` e `services/notification_service.py:9-10`
- **Evidencia:** chave de aplicacao e usuario/senha SMTP sao strings no codigo.
- **Impacto:** comprometimento de sessoes e da conta de email se os valores forem reais ou reutilizados.
- **Recomendacao:** remover/rotacionar se reais, carregar de ambiente/secret store e validar configuracao na inicializacao.

### [HIGH] Rotas concentram regras e acesso ao ORM
- **Local:** `routes/task_routes.py:12-299` e `routes/report_routes.py:1-223`
- **Evidencia:** handlers validam campos, consultam modelos, calculam dados, montam respostas e controlam transacoes.
- **Impacto:** testes unitarios e mudancas de regra dependem do contexto Flask/ORM.
- **Recomendacao:** manter routes como adaptadores HTTP e delegar orquestracao a controllers/servicos, preservando models para persistencia.

### [MEDIUM] Consulta N+1 no relatorio por usuario
- **Local:** `routes/report_routes.py:55-56`
- **Evidencia:** para cada usuario, uma query separada busca todas as tasks.
- **Impacto:** custo de acesso aumenta linearmente com os usuarios.
- **Recomendacao:** agregar no banco ou carregar tasks em lote e agrupar por `user_id`.

### [MEDIUM] Uso de APIs deprecated/legadas
- **Local:** `routes/task_routes.py:31,42,72,117` e `routes/report_routes.py:35,42,45`
- **Evidencia:** `datetime.utcnow()` e `Query.get()` aparecem no codigo. O primeiro esta deprecated no Python 3.12; `Query.get()` e legado no SQLAlchemy 2.x.
- **Impacto:** warnings e migracoes futuras mais arriscadas; timestamps naive deixam fuso implicito.
- **Recomendacao:** usar datetime UTC aware apropriado e migrar para `Session.get()` apos validar compatibilidade/semantica com testes.

### [LOW] Imports nao utilizados em helpers
- **Local:** `utils/helpers.py:3-7`
- **Evidencia:** imports `os`, `json`, `sys`, `math` e `hashlib` nao sao referenciados no modulo.
- **Impacto:** ruido e dependencias aparentes sem necessidade.
- **Recomendacao:** remover imports confirmados como nao usados.

### [LOW] Estados e limites espalhados como literais
- **Local:** `routes/task_routes.py:90-98` e `utils/helpers.py:65-70`
- **Evidencia:** status, prioridade e limites numericos aparecem inline em validacoes/helpers.
- **Impacto:** alteracoes podem divergir entre endpoints.
- **Recomendacao:** centralizar constantes/enums e reutilizar nos validadores.

## APIs deprecated
Confirmadas no codigo: `datetime.utcnow()` (Python 3.12) e `Query.get()` (SQLAlchemy 2.x). Documentacao primaria: https://docs.python.org/3.12/library/datetime.html e https://docs.sqlalchemy.org/en/20/changelog/migration_20.html.

## Gate da Fase 2
A auditoria nao alterou a logica da aplicacao. Aprovar a Fase 3 para este projeto? Aguardar resposta explicita antes de alterar codigo, configuracao da aplicacao ou dados.
