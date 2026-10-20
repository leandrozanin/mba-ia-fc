# Auditoria e Refatoracao Arquitetural com Codex

Desafio da pasta 3. A skill `refactor-arch` foi criada para Codex e copiada para os tres projetos de entrada. Os projetos vieram do repositorio publico indicado pela spec, commit `6d1ce6248c3e956801010a89d8bdaab48029bf30`.

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

A skill esta em `.agents/skills/refactor-arch/`, no formato repo-local do Codex. `SKILL.md` define as tres fases e carrega referencias Markdown para analise de projeto, catalogo de anti-patterns, template de relatorio, guidelines MVC e playbook. A mesma pasta da skill foi copiada para cada projeto para permitir invocacao local.

O catalogo cobre secrets, SQL injection, God Class, regras em handlers, estado global, transacoes, N+1, validacao, erros, APIs deprecated, magic values, codigo morto e logging. A deteccao comeca por manifestos/entry points e fluxo real, e so depois aplica sinais e mapeamento MVC idiomatico da stack. O playbook tem dez transformacoes com exemplos antes/depois.

A Fase 2 exige linhas verificadas, grava o relatorio e para pedindo aprovacao antes de alterar codigo/configuracao/dados da aplicacao. A Fase 3 requer baseline, testes, boot e verificacao dos endpoints originais.

Desafios encontrados: os projetos nao estavam no checkout e vieram do repositorio da spec; o computador nao tinha Node/npm, entao usei Node portatil 22.22.3 em pasta temporaria, sem instalacao global. Dependencias Python foram instaladas em venv locais. O Express nao declara script de teste: baseline feita por boot HTTP e chamadas representativas; tambem rodei `npm audit`.

## Resultados

| Projeto | Stack | Findings (C/H/M/L) | Total |
|---|---|---:|---:|
| 1 — code-smells-project | Python / Flask | 2 / 1 / 2 / 2 | 7 |
| 2 — ecommerce-api-legacy | Node.js / Express | 2 / 1 / 2 / 2 | 7 |
| 3 — task-manager-api | Python / Flask | 1 / 1 / 2 / 2 | 6 |

Relatorios: `reports/audit-project-1.md`, `reports/audit-project-2.md` e `reports/audit-project-3.md`.

### Estrutura antes/depois

- Projeto 1: agora usa `config/`, `views/`, controllers e models; `app.py` compoe a aplicacao e `middlewares/` centraliza erros.
- Projeto 2: agora separa `src/models/lmsRepository.js`, `src/controllers/lmsController.js` e `src/views/routes.js`; `src/app.js` compoe a aplicacao e instala middleware de erro.
- Projeto 3: preserva models/routes/services/utils e ganhou `create_app`, configuracao ambiental, handlers de erro e agregacoes para remover N+1 no relatorio.
- Senhas novas sao armazenadas com hash; health nao expoe secrets/caminhos.

### Baseline executada

- Projeto 1: 10/10 rotas GET representativas responderam 200 antes da refatoracao.
- Projeto 2: Node `v22.22.3`; relatorio e checkout responderam 200. `npm audit` original encontrou 14 vulnerabilidades.
- Projeto 3: 11 rotas GET responderam; colecoes/health deram 200 e IDs ausentes deram 404.

### Checklist de validacao

| Criterio | Projeto 1 | Projeto 2 | Projeto 3 |
|---|---|---|---|
| Fase 1: stack, dominio e contagem | [x] Python/Flask, e-commerce, 4 fontes | [x] Node/Express, LMS, 3 fontes | [x] Python/Flask, task manager, 15 fontes |
| Fase 2: relatorio, linhas, ordem, minimo 5 e HIGH/CRITICAL | [x] 7 findings | [x] 7 findings | [x] 6 findings |
| Fase 2: pausa antes de refatorar | [x] aprovada | [x] aprovada | [x] aprovada |
| Fase 3: MVC/config/seguranca | [x] config/views/controllers/models | [x] app factory + models/controllers/views + middleware | [x] app factory e camadas aprimoradas |
| Fase 3: testes | [x] 4/4 | [x] 2/2 | [x] 2/2 |
| Fase 3: boot e endpoints | [x] 10/10 GETs 200 | [x] relatorio e checkout 200 | [x] colecoes 200, IDs ausentes 404 esperados |

Evidencias: `reports/phase-3-validation.md`. O `npm audit` final ainda aponta 8 vulnerabilidades transitivas (2 low, 1 moderate, 4 high, 1 critical); corrigir todas requer atualizar `sqlite3` para a major 6. O endpoint `/admin/query` do projeto 1 retorna 410 e `/admin/reset-db` retorna 403.

## Como Executar

### Pre-requisitos

- Codex com suporte a Agent Skills e Python 3.10+.
- Projetos Flask: Python/pip e dependencias de `requirements.txt` no ambiente virtual.
- Projeto Express: Node.js 22 LTS ou versao compativel com `sqlite3`; `npm ci`.

### Invocar a skill

Abra cada projeto como workspace do Codex e solicite: `Use $refactor-arch para auditar este projeto.` A skill executa Fase 1 e Fase 2. Revise o relatorio e aprove explicitamente antes da Fase 3.

### Rodar e validar

- Projeto 1: `python app.py` (porta 5000).
- Projeto 2: `npm start` (porta 3000); exemplos em `api.http`.
- Projeto 3: `python seed.py` e `python app.py` (porta 5000).
- Rode a suite existente, inicie a API e verifique rotas/contratos registrados.
- Validar assets: `python -m unittest discover -s 3_skill_auditoria_refatoracao/tests -v`.

### Ordem sugerida

1. Analise os projetos e documente achados manualmente.
2. Crie a skill e confira as referencias.
3. Rode Fase 1 e Fase 2 em cada projeto e salve os relatorios.
4. Revise cada relatorio e aprove a Fase 3.
5. Refatore e valide um projeto por vez; atualize checklist com evidencias.
