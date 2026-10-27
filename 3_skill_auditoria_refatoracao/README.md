# Auditoria e Refatoração Arquitetural com Claude Code

Desafio 3: a skill `refactor-arch` analisa um projeto, gera um relatório de auditoria, pede aprovação e refatora o código para MVC, validando o resultado. Ela foi executada com `claude "/refactor-arch"` dentro de cada um dos três projetos legados do [repositório base](https://github.com/devfullcycle/mba-ia-refactor-projects-skill) (commit `6d1ce6248c3e956801010a89d8bdaab48029bf30`). O código em `projects/` é a saída dessas execuções.

| O quê | Onde |
|---|---|
| Skill (Claude Code) | `.claude/skills/refactor-arch/`, copiada para `projects/<projeto>/.claude/skills/refactor-arch/` |
| Skill (Codex, espelho) | `.agents/skills/refactor-arch/` |
| Código refatorado pela skill (Fase 3) | `projects/code-smells-project/`, `projects/ecommerce-api-legacy/`, `projects/task-manager-api/` |
| Código original dos projetos | tag git `original-projects` |
| Relatórios gerados pela skill (Fase 2) | `reports/audit-project-1.md`, `audit-project-2.md`, `audit-project-3.md` |
| Saída de cada execução da skill | `reports/runs/project-1.md`, `project-2.md`, `project-3.md` |
| Verificação independente da Fase 3 | `reports/phase-3-validation.md` e `reports/validation/` |

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

- **`SKILL.md` é o procedimento; as referências são o conhecimento.** O `SKILL.md` descreve só as três fases, a ordem, o gate de aprovação e os limites ("não invente linhas, endpoints ou resultados"). O conhecimento de domínio fica em cinco arquivos Markdown:

  | Área exigida | Arquivo |
  |---|---|
  | Análise de projeto | `references/project-analysis.md`: inventário de manifestos, heurísticas por stack, detecção de banco, mapeamento do fluxo de requisição |
  | Catálogo de anti-patterns | `references/anti-pattern-catalog.md`: 16 padrões (3 CRITICAL, 4 HIGH, 6 MEDIUM, 3 LOW) com sinais de detecção e regras de evidência |
  | Template de relatório | `references/audit-report-template.md`: formato fixo, ordenação por severidade, conferência das contagens, seção de APIs deprecated e gate |
  | Guidelines MVC | `references/mvc-guidelines.md`: responsabilidades das camadas, direção das dependências, mapeamento Flask/Express |
  | Playbook de refatoração | `references/refactoring-playbook.md`: 10 transformações com código antes/depois |

- **Gate explícito.** A Fase 2 termina com "Aprovar a Fase 3? (sim/não)" e o `SKILL.md` proíbe alterar código, configuração ou dados antes da aprovação.
- **Validação baseada em evidência.** A Fase 3 exige baseline antes de mexer, testes para o que mudou, boot e chamadas reais aos endpoints originais, e proíbe declarar algo resolvido sem verificar.
- **Uma skill, cópias idênticas.** A cópia da raiz é a fonte. Cada projeto tem uma cópia em `.claude/skills/refactor-arch/`, e o teste `tests/test_skill_assets.py` falha se alguma divergir.

### Anti-patterns do catálogo e por quê

Os padrões saíram da análise manual: cada problema encontrado virou um sinal de detecção acionável.

- **Segurança (CRITICAL):** segredos embutidos, SQL injection/execução arbitrária e God class, presentes nos três projetos.
- **Arquitetura (HIGH):** regra de negócio no handler, estado global/acoplamento rígido, persistência na camada de apresentação e falta de transação.
- **Qualidade (MEDIUM):** N+1, validação duplicada, falta de validação, erro opaco e **APIs deprecated**. Este último exige referência à documentação da versão em uso, como `datetime.utcnow()` no Python 3.12+ e `Query.get()` no SQLAlchemy 2.x.
- **Legibilidade (LOW):** magic values, código morto e logging improvisado.

### Como a skill é agnóstica de tecnologia

- A detecção parte de evidência do repositório (manifestos, imports, registro de rotas), não de suposições. As heurísticas cobrem Flask, Django, Express, NestJS, Java e Go.
- Os sinais do catálogo descrevem comportamento ("consulta dentro de loop", "segredo literal versionado"), não sintaxe de uma linguagem.
- As guidelines definem a separação conceitual e pedem o mecanismo idiomático da stack: Blueprints + `create_app` no Flask, Router + composition root no Express.
- A regra "arquitetura organizada ainda pode ter problemas" fez a skill auditar o comportamento do projeto 3, e não só os nomes das pastas.

### Desafios encontrados

- **Provar a execução real.** Uma primeira rodada foi feita na mesma sessão em que a skill foi escrita, sem o gate humano. Para a entrega, a skill rodou do zero em sessões novas do Claude Code: as Fases 1 e 2 pararam no gate, os relatórios foram revisados e só então a Fase 3 foi aprovada. As saídas estão em `reports/runs/`.
- **Iteração no template.** No projeto 1, a skill escreveu HIGH = 6 no resumo, mas o relatório tinha 5 blocos HIGH. A contagem foi corrigida, com nota no relatório, e o template ganhou uma regra para conferir o resumo contra os blocos.
- **Achado refutado na Fase 3.** No projeto 3, o baseline mostrou que "excluir categoria deixa tasks órfãs" era falso, porque o SQLAlchemy zera o `category_id`. A skill removeu o achado e registrou uma errata no relatório.
- **Segurança x compatibilidade.** Corrigir a falta de autenticação muda o contrato: rotas sensíveis passam a responder 401 sem token. O smoke test faz login e envia token para comprovar que, autenticados, todos os endpoints originais funcionam.
- **Ambiente Windows.** O reloader do Flask em debug cria processo filho, e o smoke test encerra a árvore inteira. Caminhos longos impediram o worktree no diretório temporário. Os logs do baseline repetiam segredos e cartões e foram mascarados.

## Resultados

### Resumo das auditorias (Fase 2)

| Projeto | Stack detectada | Domínio | Arquivos | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 1 — code-smells-project | Python 3.12 / Flask 3.1.1 + sqlite3 | E-commerce (produtos, usuários, pedidos) | 4 | 4 | 5 | 4 | 4 | **17** |
| 2 — ecommerce-api-legacy | Node.js / Express 4.22 + sqlite3 | LMS com checkout de cursos | 3 | 3 | 5 | 4 | 3 | **15** |
| 3 — task-manager-api | Python 3.12 / Flask 3.0 + Flask-SQLAlchemy 3.1 | Task Manager (tasks, usuários, categorias, relatórios) | 15 | 3 | 4 | 7 | 4 | **18** |

Todos os relatórios têm arquivo:linha em cada achado, ordem CRITICAL → LOW, seção de APIs deprecated e gate de aprovação. Houve APIs deprecated apenas no projeto 3 (`Query.get()`, `datetime.utcnow()`); nos outros a checagem está registrada, sem ocorrências.

### Estrutura antes/depois

**Projeto 1 — code-smells-project**

```
ANTES                              DEPOIS
app.py  (config + rotas + SQL      app.py                    entry point
         admin)                    loja/__init__.py          create_app (composition root)
controllers.py                     loja/config.py            configuração por ambiente
models.py (4 domínios, SQL         loja/db.py                conexão por request, schema, migração de senhas
           concatenado)            loja/models/              produto, usuario, pedido (SQL parametrizado)
database.py (conexão global)       loja/controllers/         produtos, usuarios, pedidos, relatorios, sistema
                                   loja/routes/              Blueprints HTTP
                                   loja/errors.py            erros + handlers centralizados
                                   loja/auth.py, permissoes.py, validators.py, notificacoes.py
                                   tests/test_api.py
```

**Projeto 2 — ecommerce-api-legacy**

```
ANTES                              DEPOIS
src/app.js                         src/app.js                composition root
src/AppManager.js (God Class:      src/config/index.js       configuração por ambiente (ADMIN_TOKEN obrigatório)
  DB + rotas + checkout +          src/db/database.js, schema.js
  relatório)                       src/models/               user, course, enrollment, payment, auditLog
src/utils.js (segredos, cache      src/services/             checkout, report, paymentGateway, passwordHasher
  global, "hash")                  src/controllers/          checkout, report, user + validation
                                   src/routes/index.js       Router Express
                                   src/middlewares/          adminAuth, errorHandler
                                   test/api.test.js
```

**Projeto 3 — task-manager-api** (já tinha camadas nominais; a skill completou o MVC)

```
ANTES                              DEPOIS
app.py (config fixa,               app.py                    create_app + handlers de erro
        create_all no import)      config.py                 configuração por ambiente
models/ (MD5, utcnow, Query.get)   models/                   hash com salt, regra de atraso única, constants.py
routes/ (rotas gordas:             controllers/              task, user, category, report, auth + validation, errors
  regra + ORM + N+1)               routes/                   Blueprints finos + auth.py, serializers.py, system/category
services/ (sem uso, SMTP fixo)     services/                 auth_service (token assinado), notification_service (config)
utils/helpers.py                   utils/helpers.py          utc_now e utilitários usados
seed.py                            seed.py                   usa create_app
                                   tests/                    test_security, test_tasks, test_users_reports_categories
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
| Mínimo de 5 findings | [x] 17 | [x] 15 | [x] 18 |
| APIs deprecated (se aplicável) | [x] checado, nenhuma | [x] checado, nenhuma | [x] `utcnow()`, `Query.get()` |
| Pausa e pede confirmação | [x] | [x] | [x] |
| **Fase 3** — estrutura MVC | [x] | [x] | [x] |
| Config extraída (sem hardcoded) | [x] `loja/config.py` | [x] `src/config/index.js` | [x] `config.py` |
| Models abstraem dados | [x] `loja/models/` | [x] `src/models/` | [x] `models/` |
| Views/Routes separadas | [x] `loja/routes/` | [x] `src/routes/` | [x] `routes/` |
| Controllers concentram o fluxo | [x] `loja/controllers/` | [x] `src/controllers/` + `src/services/` | [x] `controllers/` |
| Error handling centralizado | [x] `loja/errors.py` | [x] `src/middlewares/errorHandler.js` | [x] handlers em `app.py` |
| Entry point claro | [x] `app.py` | [x] `src/app.js` | [x] `app.py` |
| Aplicação inicia sem erros | [x] | [x] | [x] |
| Endpoints originais respondem | [x] 21/25 iguais; demais intencionais | [x] 7/8 iguais; 1 intencional | [x] 28/29 iguais; 1 intencional |
| Testes automatizados (criados pela skill) | [x] 30/30 | [x] 12/12 | [x] 53/53 |

### Logs da aplicação rodando após a refatoração

As tabelas completas estão em [`reports/phase-3-validation.md`](reports/phase-3-validation.md), e os logs em `reports/validation/project-N-after.server.log`. Trechos:

```text
# Projeto 1 (python app.py)
INFO loja.db: Usuário administrador inicial criado
 * Debug mode: off
"GET /usuarios HTTP/1.1" 200 -     (com token de admin)
"POST /pedidos HTTP/1.1" 201 -
"GET /usuarios HTTP/1.1" 401 -     (sem token)

# Projeto 2 (ADMIN_TOKEN=... npm start)
LMS API rodando na porta 3000...

# Projeto 3 (python seed.py && python app.py)
 * Running on http://127.0.0.1:5000
"POST /tasks HTTP/1.1" 201 -
"PUT /users/2 HTTP/1.1" 401 -      (anônimo tentando virar admin)
"PUT /users/2 HTTP/1.1" 200 -      (com token)
```

### Comportamento da skill em stacks diferentes

- **Monólito Python (projeto 1):** foi a maior transformação. Quatro arquivos planos viraram um pacote `loja/` com camadas por domínio, e o SQL injection foi corrigido em todas as queries porque elas passaram a existir só nos models. A skill também tratou a falta de autenticação com tokens e papéis.
- **Monólito Node.js (projeto 2):** os mesmos padrões apareceram em sintaxe diferente: segredo em objeto `config`, God Class, N+1 em callbacks aninhados. As guidelines levaram a soluções idiomáticas do Express. No gate, a skill perguntou como tratar a autenticação admin antes de decidir.
- **Projeto parcialmente organizado (projeto 3):** a skill não tratou as pastas existentes como prova de boa arquitetura. Encontrou rotas gordas, N+1, MD5, token falso e APIs deprecated, manteve a estrutura que fazia sentido e adicionou controllers. No baseline da Fase 3, refutou um achado da própria auditoria.
- **Pontos de atenção:** a conferência de contagens do relatório, que levou ao ajuste do template, e as limitações que a skill declarou sem esconder, listadas em `reports/phase-3-validation.md`.

## Como Executar

### Pré-requisitos

- [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) instalado e autenticado (ou Codex CLI, que usa `.agents/skills/`).
- Python 3.12+ para os projetos 1 e 3; Node.js 22+ para o projeto 2.

### Executar a skill num projeto original

O código original está na tag `original-projects`. Para rodar a skill do zero sem mexer na entrega, use um worktree num caminho curto, porque o Windows limita o tamanho dos caminhos:

```bash
git worktree add ../refactor-arch-original original-projects
cd ../refactor-arch-original/projects/code-smells-project
mkdir -p .claude/skills && cp -r ../../.claude/skills/refactor-arch .claude/skills/
claude "/refactor-arch"
```

No monorepo `mba-ia-fc`, o desafio fica na subpasta `3_skill_auditoria_refatoracao/`: use `cd ../refactor-arch-original/3_skill_auditoria_refatoracao/projects/code-smells-project`.

A skill imprime a análise (Fase 1), gera o relatório e **para pedindo aprovação** (Fase 2). Só depois de responder "sim" ela refatora e valida (Fase 3). Repita em `../ecommerce-api-legacy` e `../task-manager-api`.

### Validar o código refatorado (estado atual)

```bash
# Projeto 1
cd projects/code-smells-project
pip install -r requirements.txt
python -m unittest discover -s tests -t . -v
SECRET_KEY=<valor-longo> ADMIN_EMAIL=admin@loja.com ADMIN_PASSWORD=<senha-forte> python app.py

# Projeto 2
cd projects/ecommerce-api-legacy
npm install && npm test
ADMIN_TOKEN=<token> npm start

# Projeto 3
cd projects/task-manager-api
pip install -r requirements.txt
python -m unittest discover -s tests -t .
SECRET_KEY=<valor-longo> python seed.py && SECRET_KEY=<valor-longo> python app.py

# Smoke test dos endpoints originais (na raiz, com dependências de cada projeto em .venv/node_modules)
python scripts/smoke_test.py task-manager-api reports/validation/project-3-after.json
python scripts/smoke_test.py --compare reports/validation/project-3-baseline.json reports/validation/project-3-after.json
```

### Ordem sugerida

1. Rodar `/refactor-arch` no projeto 1, revisar o relatório e aprovar a Fase 3.
2. Repetir nos projetos 2 e 3.
3. Validar cada projeto com os testes e o smoke test acima.
