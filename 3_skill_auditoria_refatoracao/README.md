# Auditoria e Refatoração Arquitetural com Claude Code

Desafio 3: a skill `refactor-arch` analisa um projeto, gera um relatório de auditoria, pede aprovação e refatora o código para MVC, validando o resultado. Ela foi executada nos três projetos legados do [repositório base](https://github.com/devfullcycle/mba-ia-refactor-projects-skill) (commit `6d1ce6248c3e956801010a89d8bdaab48029bf30`).

| O quê | Onde |
|---|---|
| Skill (Claude Code) | `.claude/skills/refactor-arch/`, copiada para `projects/<projeto>/.claude/skills/refactor-arch/` |
| Skill (Codex, espelho) | `.agents/skills/refactor-arch/` |
| Código refatorado (resultado da Fase 3) | `projects/code-smells-project/`, `projects/ecommerce-api-legacy/`, `projects/task-manager-api/` |
| Código original dos projetos | tag git `original-projects` |
| Relatórios da Fase 2 | `reports/audit-project-1.md`, `audit-project-2.md`, `audit-project-3.md` |
| Evidências da Fase 3 | `reports/phase-3-validation.md` e `reports/validation/` |

## Análise Manual

### Projeto 1 — code-smells-project (Python/Flask, e-commerce)

- **CRITICAL — SQL arbitrario sem autenticacao**, `projects/code-smells-project/app.py:60-71`: endpoint administrativo executa o SQL do corpo HTTP e permite leitura/alteracao direta dos dados.
- **CRITICAL — segredo de sessao fixo e debug habilitado**, `projects/code-smells-project/app.py:7-8`: credencial versionada e modo debug configurado no entry point.
- **HIGH — modulo de modelos concentra dominios**, `projects/code-smells-project/models.py:1-314`: produto, usuario, pedido, SQL, regras de negocio e formatacao convivem no mesmo modulo.
- **MEDIUM — consultas N+1**, `projects/code-smells-project/models.py:171-193` e `203-225`: pedidos, itens e produtos geram consultas dentro de loops.
- **MEDIUM — validacao de produto duplicada**, `projects/code-smells-project/controllers.py:24-60` e `64-90`: create/update repetem regras com cobertura diferente.
- **LOW — listas de estados/categorias inline**, `projects/code-smells-project/controllers.py:52` e `242`: dominio fica definido dentro dos handlers.
- **LOW — logging por `print`**, `projects/code-smells-project/controllers.py:208`: mensagens sem nivel, contexto estruturado ou politica de dados.

### Projeto 2 — ecommerce-api-legacy (Node.js/Express, LMS/checkout)

- **CRITICAL — credenciais fixas e dados de pagamento em logs**, `projects/ecommerce-api-legacy/src/utils.js:2-6` e `src/AppManager.js:45`: secrets estao no fonte e o checkout imprime cartao/chave.
- **CRITICAL — dependencias vulneraveis**, `projects/ecommerce-api-legacy/package-lock.json:1563-2113`: `npm audit` encontrou 14 vulnerabilidades transitivas, incluindo 2 critical e 8 high.
- **HIGH — God Class**, `projects/ecommerce-api-legacy/src/AppManager.js:6-141`: inicializacao SQLite, rotas, checkout e relatorio estao acoplados.
- **MEDIUM — consultas N+1 no relatorio**, `projects/ecommerce-api-legacy/src/AppManager.js:89-120`: loops de cursos/matriculas disparam consultas aninhadas.
- **MEDIUM — checkout sem transacao atomica**, `projects/ecommerce-api-legacy/src/AppManager.js:50-82`: matricula, pagamento e log podem ficar parcialmente persistidos.
- **LOW — estado global mutavel**, `projects/ecommerce-api-legacy/src/utils.js:9-10`: cache e receita ficam fora do ciclo de vida da aplicacao.
- **LOW — variavel morta e abreviacoes**, `projects/ecommerce-api-legacy/src/utils.js:10` e `src/AppManager.js:29-33`: `totalRevenue` nao e usado; handler utiliza nomes curtos para dados sensiveis.

### Projeto 3 — task-manager-api (Python/Flask, task manager)

- **CRITICAL — credenciais da aplicacao/SMTP hardcoded**, `projects/task-manager-api/app.py:13` e `services/notification_service.py:9-10`: secrets versionados podem ser reutilizados fora do ambiente local.
- **HIGH — rotas concentram negocio e persistencia**, `projects/task-manager-api/routes/task_routes.py:12-299` e `routes/report_routes.py:1-223`: handlers continuam extensos e acoplados ao ORM apesar das pastas separadas.
- **MEDIUM — consulta N+1 em relatorio**, `projects/task-manager-api/routes/report_routes.py:55-56`: cada usuario causa uma query adicional de tasks.
- **MEDIUM — APIs deprecated**, `projects/task-manager-api/routes/task_routes.py:31,42,72,117` e `routes/report_routes.py:35,42,45`: `datetime.utcnow()` no Python 3.12 e `Query.get()` no SQLAlchemy 2.x.
- **LOW — imports nao usados**, `projects/task-manager-api/utils/helpers.py:3-7`: `os`, `json`, `sys`, `math` e `hashlib` nao sao referenciados.
- **LOW — estados/limites como literais**, `projects/task-manager-api/routes/task_routes.py:90-98` e `utils/helpers.py:65-70`: valores aparecem inline em validacoes.


## Construção da Skill

### Decisões de design

- **`SKILL.md` é o procedimento; as referências são o conhecimento.** O `SKILL.md` descreve só as três fases, a ordem, o gate de aprovação e os limites ("não invente linhas, endpoints ou resultados"). O conhecimento de domínio fica em cinco arquivos Markdown carregados sob demanda:

  | Área exigida | Arquivo |
  |---|---|
  | Análise de projeto | `references/project-analysis.md`: inventário de manifestos, heurísticas por stack, detecção de banco, mapeamento do fluxo de requisição |
  | Catálogo de anti-patterns | `references/anti-pattern-catalog.md`: 16 padrões (3 CRITICAL, 4 HIGH, 6 MEDIUM, 3 LOW) com sinais de detecção e regras de evidência |
  | Template de relatório | `references/audit-report-template.md`: formato fixo, ordenação por severidade, seção de APIs deprecated e gate |
  | Guidelines MVC | `references/mvc-guidelines.md`: responsabilidades das camadas, direção das dependências, mapeamento Flask/Express |
  | Playbook de refatoração | `references/refactoring-playbook.md`: 10 transformações com código antes/depois |

- **Gate explícito.** A Fase 2 termina com "Aprovar a Fase 3? (sim/não)" e o `SKILL.md` proíbe alterar código, configuração ou dados antes da aprovação.
- **Validação baseada em evidência.** A Fase 3 exige baseline antes de mexer, testes novos para o que mudou, boot e chamadas reais aos endpoints originais, e proíbe declarar algo resolvido sem verificar.
- **Uma skill, várias cópias idênticas.** A cópia da raiz é a fonte; cada projeto tem uma cópia em `.claude/skills/refactor-arch/` para funcionar com `cd <projeto> && claude "/refactor-arch"`. O teste `tests/test_skill_assets.py` falha se alguma cópia divergir.

### Anti-patterns do catálogo e por quê

Os padrões saíram da análise manual: cada problema encontrado virou um sinal de detecção acionável.

- **Segurança (CRITICAL):** segredos embutidos, SQL injection/execução arbitrária e God class. Apareceram nos três projetos e são o maior risco.
- **Arquitetura (HIGH):** regra de negócio no handler, estado global/acoplamento rígido, persistência na camada de apresentação e falta de transação. São as violações de MVC/SOLID que impedem teste e evolução.
- **Qualidade (MEDIUM):** N+1, validação duplicada, falta de validação, erro opaco e **APIs deprecated**. Este último exige referência à documentação da versão em uso, como `datetime.utcnow()` no Python 3.12+ e `Query.get()` no SQLAlchemy 2.x.
- **Legibilidade (LOW):** magic values, código morto e logging improvisado.

### Como a skill é agnóstica de tecnologia

- A detecção parte de evidência do repositório (manifestos, imports, registro de rotas), não de suposições. A tabela de heurísticas cobre Flask, Django, Express, NestJS, Java e Go.
- Os sinais do catálogo descrevem comportamento ("consulta dentro de loop", "segredo literal versionado"), não sintaxe de uma linguagem.
- As guidelines definem a separação conceitual e pedem o mecanismo idiomático da stack: Blueprints + `create_app` no Flask, Router + composition root no Express.
- A regra "arquitetura organizada ainda pode ter problemas" fez a skill auditar o comportamento do projeto 3, e não só os nomes das pastas.

### Desafios encontrados

- **Contratos HTTP.** Refatorar sem quebrar clientes exigiu um roteiro de smoke test reproduzível (`scripts/smoke_test.py`) executado antes e depois, comparando status e formato das respostas.
- **Segurança x compatibilidade.** Algumas correções mudam contrato de propósito: remover `senha` das respostas, exigir token em rotas admin, remover `/admin/query`. Cada mudança está justificada por um achado e documentada no README do projeto.
- **Express 4 + callbacks.** O `sqlite3` usa callbacks e o Express 4 não captura rejeições de handlers async. A solução foi um wrapper com Promises, transações enfileiradas sobre a conexão única e um adaptador `handle()` que encaminha erros ao middleware central.
- **Ambiente Windows.** O reloader do Flask em debug cria um processo filho, e o smoke test passou a encerrar a árvore inteira. O npm 11 bloqueia scripts de instalação, mas o binário pré-compilado do `sqlite3` funcionou.
- **Evidências sem segredos.** Os logs do baseline repetiam a chave do gateway e cartões completos, e foram mascarados antes do commit.

## Resultados

### Resumo das auditorias (Fase 2)

| Projeto | Stack detectada | Domínio | Arquivos | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 1 — code-smells-project | Python 3.12 / Flask 3.1.1 + sqlite3 | E-commerce (produtos, usuários, pedidos) | 4 | 4 | 5 | 5 | 3 | **17** |
| 2 — ecommerce-api-legacy | Node.js / Express 4.22 + sqlite3 | LMS com checkout de cursos | 3 | 2 | 6 | 4 | 3 | **15** |
| 3 — task-manager-api | Python 3.12 / Flask 3.0 + Flask-SQLAlchemy 3.1 | Task Manager (tasks, usuários, categorias, relatórios) | 15 | 2 | 4 | 6 | 3 | **15** |

Todos os relatórios têm arquivo:linha em cada achado, ordem CRITICAL → LOW, seção de APIs deprecated e gate de aprovação. As APIs deprecated foram encontradas no projeto 3; nos projetos 1 e 2 a checagem está registrada, sem ocorrências.

### Estrutura antes/depois

**Projeto 1 — code-smells-project**

```
ANTES                         DEPOIS
app.py  (config + rotas +     app.py                       composition root (create_app)
         SQL admin)           config/settings.py           configuração por ambiente
controllers.py                errors.py                    erros de aplicação
models.py (4 domínios, SQL    models/database.py           conexão por request, schema, seed
           concatenado)       models/{produto,usuario,pedido}_model.py
database.py (conexão global)  controllers/{produto,usuario,pedido,relatorio,sistema}_controller.py
                              controllers/validators.py
                              views/routes.py              Blueprint HTTP
                              middlewares/error_handler.py
                              services/notification_service.py
                              tests/test_api.py
```

**Projeto 2 — ecommerce-api-legacy**

```
ANTES                         DEPOIS
src/app.js                    src/app.js                   composition root (createApp)
src/AppManager.js (God Class: src/config/{index,logger}.js
  DB + rotas + checkout +     src/errors.js
  relatório)                  src/db/{database,seed}.js    Promises + transações
src/utils.js (segredos,       src/models/{user,course,enrollment}Model.js
  cache global, "hash")       src/controllers/{checkout,report,user}Controller.js + validators.js
                              src/services/{paymentGateway,passwordHasher}.js
                              src/views/routes.js          Router Express
                              src/middlewares/{adminAuth,errorHandler}.js
                              test/api.test.js
```

**Projeto 3 — task-manager-api** (já tinha camadas nominais; a skill completou o MVC)

```
ANTES                         DEPOIS
app.py (config fixa,          app.py                       create_app()
        create_all no import) config/settings.py           ambiente + .env
models/ (MD5, utcnow)         models/                      hash com salt, regra is_overdue única, sem utcnow
routes/ (rotas gordas:        controllers/{task,user,report,category}_controller.py + validators.py
  regra + ORM + N+1)          routes/{task,user,report,category,system}_routes.py   rotas finas
services/ (sem uso,           middlewares/{auth,error_handler}.py
  SMTP fixo)                  services/{auth_service,notification_service}.py
utils/helpers.py (código      utils/{constants,dates}.py
  morto)                      errors.py, tests/test_api.py
seed.py (apaga tudo)          seed.py                      idempotente; --reset explícito
```

### Checklist de validação

| Critério | Projeto 1 | Projeto 2 | Projeto 3 |
|---|---|---|---|
| **Fase 1** — linguagem detectada | [x] Python | [x] JavaScript (Node.js) | [x] Python |
| Framework detectado | [x] Flask 3.1.1 | [x] Express 4.22 | [x] Flask 3.0 + SQLAlchemy |
| Domínio descrito | [x] E-commerce | [x] LMS com checkout | [x] Task Manager |
| Nº de arquivos condiz | [x] 4 | [x] 3 | [x] 15 |
| **Fase 2** — segue o template | [x] | [x] | [x] |
| Arquivo e linhas exatos | [x] | [x] | [x] |
| Ordenado CRITICAL → LOW | [x] | [x] | [x] |
| Mínimo de 5 findings | [x] 17 | [x] 15 | [x] 15 |
| APIs deprecated (se aplicável) | [x] checado, nenhuma | [x] checado, nenhuma | [x] `utcnow()`, `Query.get()` |
| Pausa e pede confirmação | [x] | [x] | [x] |
| **Fase 3** — estrutura MVC | [x] | [x] | [x] |
| Config extraída (sem hardcoded) | [x] `config/settings.py` | [x] `src/config/` | [x] `config/settings.py` |
| Models abstraem dados | [x] `models/` | [x] `src/models/` | [x] `models/` |
| Views/Routes separadas | [x] `views/routes.py` | [x] `src/views/routes.js` | [x] `routes/` |
| Controllers concentram o fluxo | [x] `controllers/` | [x] `src/controllers/` | [x] `controllers/` |
| Error handling centralizado | [x] `middlewares/error_handler.py` | [x] `src/middlewares/errorHandler.js` | [x] `middlewares/error_handler.py` |
| Entry point claro | [x] `app.py` | [x] `src/app.js` | [x] `app.py` |
| Aplicação inicia sem erros | [x] | [x] | [x] |
| Endpoints originais respondem | [x] 22/24 iguais, 2 bloqueios intencionais | [x] 8/9 iguais, 1 bloqueio intencional | [x] 29/30 iguais, 1 bloqueio intencional |
| Testes automatizados | [x] 17/17 | [x] 10/10 | [x] 16/16 |

### Logs da aplicação rodando após a refatoração

As tabelas completas de antes/depois estão em [`reports/phase-3-validation.md`](reports/phase-3-validation.md), e os logs do servidor em `reports/validation/project-N-after.server.log`. Trechos:

```text
# Projeto 1 (python app.py)
INFO __main__: Servidor em http://127.0.0.1:5000
 * Debug mode: off
INFO werkzeug: 127.0.0.1 - - "GET /produtos HTTP/1.1" 200 -
INFO werkzeug: 127.0.0.1 - - "POST /pedidos HTTP/1.1" 201 -
INFO werkzeug: 127.0.0.1 - - "POST /admin/query HTTP/1.1" 404 -

# Projeto 2 (npm start)
INFO LMS API rodando na porta 3000
INFO Pagamento PAID para curso 1 (cartão final 1111)

# Projeto 3 (python seed.py && python app.py)
INFO werkzeug: 127.0.0.1 - - "GET /tasks HTTP/1.1" 200 -
INFO werkzeug: 127.0.0.1 - - "PUT /users/2 HTTP/1.1" 401 -
INFO werkzeug: 127.0.0.1 - - "DELETE /categories/4 HTTP/1.1" 200 -
```

### Comportamento da skill em stacks diferentes

- **Monólito Python (projeto 1):** foi a maior transformação. Quatro arquivos planos viraram camadas por domínio, e a correção de SQL injection foi aplicada em todas as queries de uma vez, porque passaram a existir só nos models.
- **Monólito Node.js (projeto 2):** o catálogo encontrou os mesmos padrões em sintaxe diferente: segredo em objeto `config`, God Class, N+1 em callbacks aninhados. As guidelines levaram a soluções idiomáticas do Express (Router, middleware de erro, factory com injeção do gateway de pagamento).
- **Projeto parcialmente organizado (projeto 3):** a skill não tratou as pastas existentes como prova de boa arquitetura. Apontou rotas gordas, N+1, MD5, token falso e APIs deprecated, preservou a estrutura que já fazia sentido (`models/`, `routes/`, `services/`) e adicionou a camada de controllers.
- **Limitações registradas:** `npm audit` no projeto 2 aponta vulnerabilidades transitivas que exigem `sqlite3@6` (breaking); no projeto 3, a escrita de tasks continua pública, como no original.

## Como Executar

### Pré-requisitos

- [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) instalado e autenticado (ou Codex CLI, que usa `.agents/skills/`).
- Python 3.12+ para os projetos 1 e 3; Node.js 22+ para o projeto 2.

### Validar o código refatorado (estado atual)

```bash
# Projeto 1
cd projects/code-smells-project
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # Linux/macOS: .venv/bin/pip
.venv/Scripts/python -m unittest discover -s tests -v
SECRET_KEY=dev .venv/Scripts/python app.py

# Projeto 2
cd projects/ecommerce-api-legacy
npm install && npm test
ADMIN_API_TOKEN=dev-token npm start

# Projeto 3
cd projects/task-manager-api
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python -m unittest discover -s tests -v
.venv/Scripts/python seed.py && .venv/Scripts/python app.py

# Smoke test comparando com o baseline do código original (na raiz)
python scripts/smoke_test.py task-manager-api reports/validation/project-3-after.json
python scripts/smoke_test.py --compare reports/validation/project-3-baseline.json reports/validation/project-3-after.json
```

### Executar a skill do zero num projeto original

O código original está preservado na tag `original-projects`. Para rodar a skill desde o início sem perder o resultado entregue, use um worktree:

```bash
git worktree add ../refactor-arch-original original-projects
cd ../refactor-arch-original/3_skill_auditoria_refatoracao/projects/code-smells-project
mkdir -p .claude/skills && cp -r ../../.claude/skills/refactor-arch .claude/skills/   # a tag é anterior às cópias
claude "/refactor-arch"
```

A skill imprime a análise (Fase 1), gera o relatório e **para pedindo aprovação** (Fase 2). Só depois de responder "sim" ela refatora e valida (Fase 3). Repita para `../ecommerce-api-legacy` e `../task-manager-api`.

### Ordem sugerida

1. Rodar `/refactor-arch` no projeto 1, revisar o relatório e aprovar a Fase 3.
2. Repetir nos projetos 2 e 3.
3. Validar cada projeto com os testes e o smoke test acima.
