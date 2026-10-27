# Relatório de Auditoria — task-manager-api

## Análise do projeto
- **Linguagem/framework:** Python 3.12.10 (`.venv/pyvenv.cfg`) / Flask 3.0.0 — `Flask(__name__)` em `app.py:9`, três Blueprints (`task_bp`, `user_bp`, `report_bp`) registrados em `app.py:18-20`.
- **Banco e dependências relevantes:** SQLite via Flask-SQLAlchemy 3.1.1 (`app.py:11`, `database.py:3`); SQLAlchemy instalado no venv: 2.1.6 (não fixado em `requirements.txt`). Flask-CORS 4.0.0 em uso. `marshmallow`, `requests` e `python-dotenv` estão declarados em `requirements.txt`, mas nenhum arquivo-fonte os importa.
- **Domínio:** gerenciador de tarefas — usuários (`User`), categorias (`Category`) e tarefas (`Task`) com status, prioridade 1–5, prazo, tags, além de relatórios de produtividade.
- **Arquitetura atual:** MVC parcial. Existem pastas `models/`, `routes/`, `services/` e `utils/`, mas as rotas fazem validação, regra de negócio, queries e serialização direto no handler. `services/` e a maior parte de `utils/` não são usados por nenhuma rota. Não há app factory nem camada de configuração.
  Fluxo de uma requisição: `routes/*` (Blueprint) → validação inline → `Model.query` / `db.session` → `jsonify`.
- **Arquivos-fonte analisados / excluídos:** 15 arquivos `.py` analisados (`app.py`, `database.py`, `seed.py`, `models/{__init__,task,user,category}.py`, `routes/{__init__,task_routes,user_routes,report_routes}.py`, `services/{__init__,notification_service}.py`, `utils/{__init__,helpers}.py`), mais `requirements.txt` e `README.md`. Excluídos: `.venv/` (dependências) e `.claude/` (a própria skill).
- **Comandos de teste e boot disponíveis:** não há testes nem configuração de testes. Boot (pelo README): `pip install -r requirements.txt`, `python seed.py`, `python app.py` → `http://localhost:5000`.
- **Endpoints (22, tirados dos decorators de rota):**
  - `app.py`: `GET /`, `GET /health`
  - `routes/task_routes.py`: `GET /tasks`, `POST /tasks`, `GET /tasks/<id>`, `PUT /tasks/<id>`, `DELETE /tasks/<id>`, `GET /tasks/search`, `GET /tasks/stats`
  - `routes/user_routes.py`: `GET /users`, `POST /users`, `GET /users/<id>`, `PUT /users/<id>`, `DELETE /users/<id>`, `GET /users/<id>/tasks`, `POST /login`
  - `routes/report_routes.py`: `GET /reports/summary`, `GET /reports/user/<id>`, `GET /categories`, `POST /categories`, `PUT /categories/<id>`, `DELETE /categories/<id>`

## Resumo
| Severidade | Quantidade |
|---|---:|
| CRITICAL | 3 |
| HIGH | 4 |
| MEDIUM | 7 |
| LOW | 4 |
| **Total** | **18** |

> **Errata (Fase 3):** a versão inicial listava “Excluir categoria deixa tarefas com FK órfã” (MEDIUM). O baseline mostrou que é falso: ao excluir a categoria, o SQLAlchemy carrega o backref `Category.tasks` e define `category_id = NULL` nas tarefas (`GET /tasks/4` passa a retornar `category_id: null`). O achado foi removido.

## Achados

### [CRITICAL] Segredos embutidos no código
- **Local:** `app.py:13`; `services/notification_service.py:9-10`
- **Evidência:** `app.config['SECRET_KEY']` recebe uma string literal; `NotificationService.__init__` define `self.email_user` e `self.email_password` como literais (credenciais SMTP do Gmail). Os valores foram omitidos aqui de propósito.
- **Descrição:** a chave de assinatura do Flask e as credenciais de e-mail estão versionadas no código-fonte.
- **Impacto:** quem tiver acesso ao repositório pode forjar cookies de sessão assinados e usar a conta SMTP. Para trocar os segredos é preciso alterar o código.
- **Recomendação:** ler de variáveis de ambiente (o `python-dotenv` já está declarado), falhar no boot se estiverem ausentes, rotacionar as credenciais se forem reais e não registrá-las em logs.

### [CRITICAL] Hash de senha exposto nas respostas da API
- **Local:** `models/user.py:21`; usado em `routes/user_routes.py:33`, `:85`, `:129`, `:209`
- **Evidência:** `User.to_dict()` inclui `'password': self.password`. Esse dicionário é retornado por `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`.
- **Descrição:** o hash da senha de qualquer usuário é devolvido no JSON, e `GET /users/<id>` não exige autenticação.
- **Impacto:** combinado com o MD5 sem salt (achado HIGH abaixo), qualquer cliente pode enumerar IDs, coletar os hashes e quebrá-los offline em pouco tempo.
- **Recomendação:** remover `password` da serialização pública e usar um schema de saída explícito (o `marshmallow` já está declarado).

### [CRITICAL] Sem autenticação/autorização; token falsificável e escalada de privilégio
- **Local:** `routes/user_routes.py:210`; `routes/user_routes.py:52`, `:71-72`, `:119-122`; todas as rotas de escrita
- **Evidência:** o login retorna `'fake-jwt-token-' + str(user.id)`, que nenhuma rota valida. `POST /users` aceita `role` vindo do corpo, incluindo `admin`. Nenhuma rota verifica identidade ou papel (`User.is_admin` em `models/user.py:34` nunca é chamado).
- **Descrição:** qualquer cliente anônimo pode criar administradores, mudar o papel de qualquer usuário, desativá-lo ou apagá-lo (junto com as tarefas), e editar tarefas e categorias.
- **Impacto:** controle de acesso inexistente; o “token” é previsível a partir do ID.
- **Recomendação:** autenticação real (JWT assinado ou sessão), decorator/middleware de autorização por papel, e `role` atribuível só por administradores.

### [HIGH] Senhas com MD5 sem salt
- **Local:** `models/user.py:29`, `models/user.py:32`
- **Evidência:** `hashlib.md5(pwd.encode()).hexdigest()` em `set_password` e `check_password`; mínimo de 4 caracteres em `routes/user_routes.py:64`.
- **Descrição:** MD5 é rápido e, sem salt, senhas iguais geram hashes iguais.
- **Impacto:** é fácil quebrar por força bruta ou tabelas pré-computadas, principalmente com senhas de 4 caracteres.
- **Recomendação:** `werkzeug.security.generate_password_hash`/`check_password_hash` (já é dependência do Flask) ou bcrypt/argon2, com re-hash no próximo login e uma política mínima de senha mais forte.

### [HIGH] Servidor de desenvolvimento com debug exposto na rede
- **Local:** `app.py:34`
- **Evidência:** `app.run(debug=True, host='0.0.0.0', port=5000)`
- **Descrição:** o debugger interativo do Werkzeug fica ativo e escutando em todas as interfaces.
- **Impacto:** se alguém na rede conseguir o PIN do debugger ou ele vazar, consegue executar código arbitrário no processo. Stack traces também ficam expostos.
- **Recomendação:** debug e host vindos de configuração (desligado por padrão) e servidor WSGI de produção.

### [HIGH] Regra de negócio e persistência nas rotas
- **Local:** `routes/report_routes.py:12-101`; `routes/task_routes.py:11-63`, `:85-154`, `:273-299`; `routes/user_routes.py:42-90`
- **Evidência:** `summary_report` faz 15 consultas, calcula atrasos, taxa de conclusão e produtividade por usuário dentro do handler. `create_task`/`update_task` validam, consultam FKs, convertem datas/tags e fazem commit no handler.
- **Descrição:** as rotas acumulam o papel de adaptador HTTP, validador, serviço de domínio e repositório. A camada `services/` existe mas nenhuma rota a usa.
- **Impacto:** regras de negócio não podem ser testadas sem HTTP, há duplicação (ver achados MEDIUM) e qualquer mudança de regra exige editar vários handlers.
- **Recomendação:** extrair controllers/serviços (`TaskService`, `ReportService`, `UserService`) e consultas para os models/repositórios, deixando a rota só com parse da requisição → chamada → resposta.

### [HIGH] Acoplamento rígido: app global, configuração fixa e efeito colateral no import
- **Local:** `app.py:9-31`; `seed.py:2`; `services/notification_service.py:6`
- **Evidência:** `app` é criado no nível do módulo com URI de banco e configuração literais; `db.create_all()` roda no import (`app.py:30-31`); `seed.py` importa `app` diretamente; `NotificationService` guarda notificações numa lista em memória da instância.
- **Descrição:** não há app factory nem configuração por ambiente; importar `app` já cria o schema no banco real `tasks.db`.
- **Impacto:** testes não conseguem isolar o banco (ex.: SQLite temporário) sem mexer no módulo; as notificações se perdem a cada reinício e não são compartilhadas entre workers.
- **Recomendação:** `create_app(config)` com configuração vinda do ambiente, criação de schema explícita (comando/migration) e injeção de dependências dos serviços.

### [MEDIUM] CORS liberado para qualquer origem
- **Local:** `app.py:15`
- **Evidência:** `CORS(app)` sem parâmetros.
- **Descrição:** todas as rotas aceitam requisições cross-origin de qualquer site.
- **Impacto:** somado à ausência de autenticação, qualquer página web pode chamar as rotas de escrita a partir do navegador da vítima na rede interna.
- **Recomendação:** allowlist de origens vinda de configuração.

### [MEDIUM] Query N+1 e contagens repetidas
- **Local:** `routes/task_routes.py:42`, `:51`; `routes/user_routes.py:22`; `routes/report_routes.py:56`, `:163`; `routes/report_routes.py:15-28`; `routes/task_routes.py:275-281`
- **Evidência:** `User.query.get(t.user_id)` e `Category.query.get(t.category_id)` dentro do loop de tarefas; `len(u.tasks)` (lazy load) por usuário; `Task.query.filter_by(user_id=u.id)` e `filter_by(category_id=c.id).count()` dentro de loops. O summary faz uma consulta `count()` por status e por prioridade e ainda carrega todas as tarefas.
- **Descrição:** o número de consultas cresce com o número de linhas; não há paginação em `GET /tasks`.
- **Impacto:** a latência cresce linearmente com o volume de dados.
- **Recomendação:** `joinedload`/`selectinload`, agregações com `GROUP BY` (`func.count`, `case`), filtro de atrasados no SQL e paginação.

### [MEDIUM] Validação e regras duplicadas/inconsistentes
- **Local:** status válidos em `routes/task_routes.py:110`, `:177`, `models/task.py:39`, `utils/helpers.py:75`, `:110`; cálculo de “atrasada” em `routes/task_routes.py:30-39`, `:71-80`, `:283-287`, `routes/user_routes.py:171-180`, `routes/report_routes.py:34-36`, `:132-135` (e `models/task.py:50-60`, não usado); serialização manual de `Task` em `routes/task_routes.py:17-28` e `routes/user_routes.py:162-169`
- **Evidência:** a mesma regra aparece copiada em 6 lugares. `utils/helpers.py:57-108` (`process_task_data`) faz `strip()`, converte prioridade com `int()` e aceita `dd/mm/YYYY`, enquanto as rotas não fazem nada disso. `create_task` responde “Formato de data inválido. Use YYYY-MM-DD” e `update_task` responde só “Formato de data inválido”.
- **Descrição:** existem várias versões da mesma regra, com resultados diferentes.
- **Impacto:** uma correção feita num lugar não chega aos outros; create e update aceitam entradas diferentes; `/users/<id>/tasks` devolve um formato de tarefa diferente de `/tasks`.
- **Recomendação:** um validador/schema compartilhado para criar e atualizar, `Task.is_overdue()` como única fonte da regra e um único serializador.

### [MEDIUM] Falta de validação de tipos na entrada (500 em vez de 400)
- **Local:** `routes/task_routes.py:96`, `:113`, `:167`, `:182`, `:261`, `:264`; `routes/report_routes.py:196-197`; `routes/user_routes.py:102-103`, `:124-125`; `routes/report_routes.py:180`, `:202`
- **Evidência:** `priority < 1` com uma string (`"priority": "a"`) gera `TypeError`; `len(title)` com um número gera `TypeError`; `int(priority)` em `/tasks/search?priority=x` gera `ValueError`; `update_category` faz `'name' in data` sem checar se `data` é `None` (com corpo JSON `null`). Nenhum desses casos tem tratamento, então a resposta é 500 — confirmado no baseline da Fase 3 para `priority: "a"`, `title: 12345`, `/tasks/search?priority=x` e `PUT /categories/1` com corpo `null`. `name` pode virar vazio no update, `active` aceita qualquer tipo e `color` não é validada (`is_valid_color` existe, mas não é usada).
- **Descrição:** a entrada é usada sem checagem de tipo ou formato.
- **Impacto:** entrada inválida do cliente vira erro 500 em vez de 400, e dados malformados podem ser gravados.
- **Recomendação:** validar na fronteira com um schema (marshmallow) e responder 400 com mensagens consistentes.

### [MEDIUM] Tratamento de erro opaco (`except:` genérico)
- **Local:** `routes/task_routes.py:62`, `:137`, `:204`, `:236`; `routes/user_routes.py:130`, `:149`; `routes/report_routes.py:186`, `:207`, `:221`; `utils/helpers.py:46`, `:49`, `:88`; `services/notification_service.py:23-25`
- **Evidência:** `except:` sem classe, que também captura `KeyboardInterrupt`/`SystemExit`. `GET /tasks` troca qualquer falha por `{'error': 'Erro interno'}` sem registrar nada. `send_email` engole a exceção e retorna `False`, e quem chama ignora o retorno.
- **Descrição:** erros são escondidos sem log útil, ou só aparecem num `print`.
- **Impacto:** fica difícil diagnosticar falhas em produção, e falhas de envio de e-mail passam despercebidas.
- **Recomendação:** capturar exceções específicas (`SQLAlchemyError`, `ValueError`), usar `errorhandler` central com `logging` e propagar ou registrar a falha de notificação.

### [MEDIUM] API deprecated: `Query.get()` (SQLAlchemy 2.x)
- **Local:** `routes/task_routes.py:42`, `:51`, `:67`, `:117`, `:122`, `:158`, `:188`, `:195`, `:227`; `routes/user_routes.py:29`, `:94`, `:136`, `:155`; `routes/report_routes.py:105`, `:192`, `:213`
- **Evidência:** `Model.query.get(id)`. No SQLAlchemy 2.1.6 instalado, `sqlalchemy/orm/query.py:1061-1064` marca `Query.get` como legado com a alternativa “now available as `Session.get`”, e ele emite `LegacyAPIWarning`.
- **Descrição:** a API está marcada como legado/deprecated na versão em uso.
- **Impacto:** avisos em runtime e risco de quebra numa atualização; o SQLAlchemy também não está fixado em `requirements.txt`, então a versão instalada pode mudar.
- **Recomendação:** `db.session.get(Model, id)` (ou `db.get_or_404`) e fixar `SQLAlchemy` no manifesto.

### [MEDIUM] API deprecated: `datetime.utcnow()` (Python 3.12)
- **Local:** `models/task.py:15`, `:16`, `:52`; `models/user.py:14`; `models/category.py:11`; `routes/task_routes.py:31`, `:72`, `:215`, `:285`; `routes/user_routes.py:172`; `routes/report_routes.py:35`, `:42`, `:45`, `:71`, `:133`; `services/notification_service.py:35`; `utils/helpers.py:38`; `seed.py:66-74`
- **Evidência:** o runtime do projeto é Python 3.12.10, e a documentação do Python 3.12 marca `datetime.datetime.utcnow()` como deprecated (emite `DeprecationWarning`), recomendando `datetime.now(datetime.UTC)`.
- **Descrição:** uso de uma API deprecated no runtime atual, gerando datetimes “naive”. Além disso, `/health` (`app.py:24`) usa `datetime.now()` local, misturando fusos.
- **Impacto:** warnings e, numa migração para datetimes com fuso, comparações entre naive e aware lançam `TypeError` (ex.: `due_date < agora`).
- **Recomendação:** um helper `utc_now()` com `datetime.now(UTC)`, migrado de forma consistente nos models, nas rotas e na comparação de prazos, com teste.

### [LOW] Magic numbers/strings espalhados
- **Local:** `routes/task_routes.py:96-114`; `routes/user_routes.py:64`, `:71`; `routes/report_routes.py:24-28`, `:84-88`, `:129`; `models/task.py:11-12`
- **Evidência:** `3`/`200` (tamanho do título), `1..5` (prioridade), `4` (senha), listas de status/papéis e o mapeamento prioridade→rótulo (`1→critical` … `5→minimal`) escritos direto no código. As constantes `VALID_STATUSES`, `VALID_ROLES`, `MAX_TITLE_LENGTH` etc. existem em `utils/helpers.py:110-116`, mas nenhum arquivo as importa.
- **Descrição:** valores de domínio repetidos sem nome.
- **Impacto:** é fácil que os valores divirjam (já há divergência, ver validação duplicada).
- **Recomendação:** um `Enum`/constantes de domínio num único módulo, usados por models, validação e relatórios.

### [LOW] Código morto e imports não usados
- **Local:** `app.py:7`; `routes/task_routes.py:7`; `routes/user_routes.py:6`; `routes/report_routes.py:7-8`; `models/task.py:3`; `utils/helpers.py:3-7`, `:9-55`, `:57-108`; `models/task.py:38-60`; `models/user.py:34-38`; `services/notification_service.py` (todo o arquivo)
- **Evidência:** `os, sys, json, time, hashlib` importados e não usados; `format_date` e `calculate_percentage` importados em `report_routes.py:7` mas não chamados. `process_task_data`, `validate_email`, `sanitize_string`, `generate_id`, `log_action`, `parse_date`, `is_valid_color`, `Task.validate_status/validate_priority/is_overdue`, `User.is_admin` e `NotificationService` não são referenciados por nenhum outro módulo (checado com busca no projeto).
- **Descrição:** existe código que parece reutilizável, mas está desconectado do fluxo real.
- **Impacto:** confunde a manutenção, porque um leitor pode supor que essas regras estão em vigor.
- **Recomendação:** ligar o que for útil (validação, `is_overdue`) na refatoração e remover o resto.

### [LOW] Logging improvisado com `print`
- **Local:** `routes/task_routes.py:149`, `:153`, `:219`, `:234`; `routes/user_routes.py:83`, `:89`, `:147`; `services/notification_service.py:21`, `:24`; `utils/helpers.py:39-41`
- **Evidência:** `print(f"Usuário criado: {user.id} - {user.name}")`, `print(f"ERRO: {str(e)}")`, `print(f"Email enviado para {to}")`.
- **Descrição:** saída sem nível, sem estrutura e com dados pessoais (nome, e-mail).
- **Impacto:** não dá para filtrar ou rotear os logs, e há vazamento de dados pessoais no stdout.
- **Recomendação:** `logging`/`app.logger` com níveis e sem dados pessoais desnecessários.

### [LOW] Rotas de categorias no blueprint de relatórios
- **Local:** `routes/report_routes.py:157-223`
- **Evidência:** o CRUD de `/categories` está registrado em `report_bp`.
- **Descrição:** as responsabilidades estão agrupadas de forma incoerente.
- **Impacto:** fica difícil encontrar o código e evoluir os dois domínios separadamente.
- **Recomendação:** mover para um `category_bp`/controller próprio, mantendo as mesmas URLs.

## APIs deprecated
- **`Query.get()`** — legado no SQLAlchemy 2.x; confirmado no código instalado (`.venv/.../sqlalchemy/orm/query.py:1061-1064`, versão 2.1.6). 16 chamadas no código da aplicação (detalhes no achado MEDIUM).
- **`datetime.utcnow()`** — deprecated a partir do Python 3.12 (runtime do projeto: 3.12.10). Usado em models, rotas, serviço, helpers e seed.
- Checagem adicional: nenhum uso de `before_first_request`, `flask.json.JSONEncoder`, `_app_ctx_stack`/`_request_ctx_stack` ou `Model.query.get_or_404` legado foi encontrado. Não há alegação de CVE para as dependências: nenhum scanner (`pip-audit`) foi executado nesta auditoria.

## Limitações
- A auditoria foi estática: a aplicação não foi iniciada e não há testes no projeto. Os erros 500 foram depois confirmados no baseline da Fase 3 (test client); ver a errata no Resumo.

## Gate da Fase 2
A auditoria não alterou o código-alvo; o único arquivo criado foi este relatório. **Fase 3 aprovada em 2026-10-26.**

## Resultado da Fase 3

### Validação
| Etapa | Comando | Resultado |
|---|---|---|
| Baseline | sondagem de 56 requisições (test client) no código original, cópia isolada | registrado; 4 respostas 500 (HTML) |
| Testes | `python -m unittest discover -s tests -t .` | 53 testes, OK (antes: nenhum teste) |
| Comparação | mesma sondagem no código refatorado | 46/56 idênticas; 10 diferenças, todas intencionais (abaixo) |
| Deprecações | sondagem com `-W error::DeprecationWarning` + teste dedicado | nenhum warning |
| Boot | `python seed.py` + `python app.py` com SQLite temporário, 22 endpoints via HTTP | todos com o status esperado; sem `SECRET_KEY` o boot falha com `ConfigError` |

### Mudanças de contrato (intencionais)
- O campo `password` saiu das respostas de `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`.
- `token` agora é assinado (itsdangerous, com validade); o formato `fake-jwt-token-N` é rejeitado.
- Rotas de escrita exigem `Authorization: Bearer <token>` (401/403 conforme o README).
- Entrada inválida responde 400 em JSON em vez de 500 HTML: `priority` não inteira, `title` não string, `?priority=x`/`?user_id=x` e corpo `null`.
- A senha mínima passou de 4 para 8 caracteres; a mensagem de data no `PUT /tasks` virou a mesma do `POST`; `color` deve ser `#RRGGBB`; `active` deve ser booleano.
- CORS fica desligado sem `CORS_ORIGINS`; o servidor sobe em `127.0.0.1` com debug desligado.

### Estrutura
Antes: `app.py` (app global + config fixa) → `routes/*` (HTTP + validação + regra + SQL); `services/` e `utils/` desconectados.
Depois: `app.py` (`create_app`, error handlers) → `routes/*` (HTTP, auth, serialização) → `controllers/*` (casos de uso, validação, transação) → `models/*` (dados, `Task.is_overdue`/`overdue_filter`, constantes) e `services/*` (token, SMTP); `config.py` lê o ambiente.

### Limitações
- As rotas `GET` continuam públicas (incluindo e-mails em `GET /users`), para preservar o contrato de leitura.
- `NotificationService` agora lê as credenciais da configuração, mas segue sem uso por nenhuma rota.
- `marshmallow` e `requests` continuam declarados e sem uso; nenhum scanner de dependências (`pip-audit`) foi executado.
- Hashes MD5 legados são migrados só quando o usuário faz login. As senhas de exemplo do `seed.py` continuam curtas (são dados de desenvolvimento).
- Não há rate limiting no `/login`.
