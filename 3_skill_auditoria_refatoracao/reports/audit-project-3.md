# Relatório de Auditoria — task-manager-api

## Análise do projeto
- **Linguagem/framework:** Python / Flask com Flask-SQLAlchemy. Evidência: `app.py:1,9` (`Flask(__name__)`), Blueprints registrados em `app.py:18-20` e definidos em `routes/task_routes.py:9`, `routes/user_routes.py:8`, `routes/report_routes.py:10`; models declarativos `db.Model` em `models/*.py`. `requirements.txt` fixa `flask==3.0.0`, `flask-sqlalchemy==3.1.1`, `flask-cors==4.0.0`, `marshmallow==3.20.1`, `requests==2.31.0`, `python-dotenv==1.0.0`.
- **Banco e dependências relevantes:** SQLite via SQLAlchemy, URI fixa `sqlite:///tasks.db` (`app.py:11`); schema criado por `db.create_all()` no import do módulo (`app.py:30-31`), sem migrations. Relações `Task → User` e `Task → Category` por FK com `backref` (`models/task.py:13-14,20-21`). `marshmallow`, `requests` e `python-dotenv` são declarados mas **não importados em nenhum arquivo**. `smtplib` usado apenas em `services/notification_service.py`, que não é referenciado pela aplicação.
- **Domínio:** gerenciador de tarefas — usuários (CRUD + login), tasks (CRUD, busca, estatísticas, atraso), categorias (CRUD) e relatórios (resumo geral e por usuário).
- **Arquitetura atual:** camadas nominais (`models/`, `routes/`, `services/`, `utils/`), mas na prática **rotas gordas**: validação, regras (atraso, estatísticas, produtividade), serialização e acesso a dados estão nos handlers. `services/` e a maior parte de `utils/` não são usados. Fluxo:
  ```
  app.py (config fixa + CORS + register_blueprint + create_all)
     └─> routes/*.py (parse HTTP + validação + regras + queries ORM + serialização)
            └─> models/*.py (colunas + to_dict + métodos de regra não usados)
                   └─> database.py (SQLAlchemy() global)
  services/notification_service.py, utils/helpers.py (exceto 2 imports não usados) → sem consumidores
  seed.py → importa app e apaga/recria dados
  ```
- **Arquivos-fonte analisados / excluídos:** 15 arquivos Python inspecionados (12 com conteúdo + 3 `__init__.py` vazios em `routes/`, `services/`, `utils/`): `app.py` (34 linhas), `database.py` (3), `seed.py` (99), `models/__init__.py` (3), `models/task.py` (60), `models/user.py` (38), `models/category.py` (21), `routes/task_routes.py` (299), `routes/user_routes.py` (211), `routes/report_routes.py` (223), `services/notification_service.py` (48), `utils/helpers.py` (116) — total ≈ 1.155 linhas; mais `requirements.txt` e `README.md`. Excluídos: nenhum (não há `.venv`, caches ou `tasks.db` no diretório).
- **Comandos de teste e boot disponíveis:** `pip install -r requirements.txt && python seed.py && python app.py` (README), sobe em `0.0.0.0:5000` com `debug=True` (`app.py:34`). **Não há testes.** Limitação: nesta fase a aplicação não foi executada; análise estática.

### Endpoints (a partir dos decorators reais)
| Método | Rota | Handler |
|---|---|---|
| GET | `/` | `app.index` |
| GET | `/health` | `app.health` |
| GET | `/tasks` | `get_tasks` |
| GET | `/tasks/<int:task_id>` | `get_task` |
| POST | `/tasks` | `create_task` |
| PUT | `/tasks/<int:task_id>` | `update_task` |
| DELETE | `/tasks/<int:task_id>` | `delete_task` |
| GET | `/tasks/search` | `search_tasks` (`q`, `status`, `priority`, `user_id`) |
| GET | `/tasks/stats` | `task_stats` |
| GET | `/users` | `get_users` |
| GET | `/users/<int:user_id>` | `get_user` |
| POST | `/users` | `create_user` |
| PUT | `/users/<int:user_id>` | `update_user` |
| DELETE | `/users/<int:user_id>` | `delete_user` |
| GET | `/users/<int:user_id>/tasks` | `get_user_tasks` |
| POST | `/login` | `login` |
| GET | `/reports/summary` | `summary_report` |
| GET | `/reports/user/<int:user_id>` | `user_report` |
| GET | `/categories` | `get_categories` |
| POST | `/categories` | `create_category` |
| PUT | `/categories/<int:cat_id>` | `update_category` |
| DELETE | `/categories/<int:cat_id>` | `delete_category` |

## Resumo
| Severidade | Quantidade |
|---|---:|
| CRITICAL | 2 |
| HIGH | 4 |
| MEDIUM | 6 |
| LOW | 3 |
| **Total** | **15** |

## Achados

### [CRITICAL] Segredos embutidos no código
- **Local:** `app.py:13`, `services/notification_service.py:9-10`
- **Evidência:** `app.config['SECRET_KEY']` com literal fixo (`app.py:13`); usuário e senha SMTP como literais em `NotificationService.__init__` (`services/notification_service.py:9-10`). Valores omitidos neste relatório.
- **Descrição:** A chave de assinatura do Flask e credenciais de e-mail estão versionadas. `python-dotenv` está nas dependências, mas não é usado.
- **Impacto:** Quem tem acesso ao repositório pode forjar sessões assinadas pelo Flask e usar a conta SMTP.
- **Recomendação:** Carregar `SECRET_KEY`, URI do banco e credenciais SMTP de variáveis de ambiente (opcionalmente via `python-dotenv`), sem defaults secretos; rotacionar os valores atuais se forem reais.

### [CRITICAL] Hash de senha MD5 sem salt exposto pela API
- **Local:** `models/user.py:21`, `models/user.py:27-32`, `routes/user_routes.py:33`, `routes/user_routes.py:85`, `routes/user_routes.py:129`, `routes/user_routes.py:209`, `seed.py:19,26,33`
- **Evidência:** `User.to_dict()` inclui `'password': self.password` (`models/user.py:21`); `set_password` usa `hashlib.md5(pwd.encode()).hexdigest()` sem salt (`models/user.py:29`) e `check_password` compara com `==` (`:32`). `to_dict()` é retornado por `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`. O seed cria contas (inclusive `admin`) com senhas curtíssimas fixas no código (valores omitidos).
- **Descrição:** O hash da senha de qualquer usuário é entregue a qualquer cliente sem autenticação, e MD5 sem salt é revertido por tabelas pré-computadas em segundos para senhas fracas (o mínimo aceito é 4 caracteres, `routes/user_routes.py:64`).
- **Impacto:** Recuperação das senhas reais de todos os usuários, incluindo o admin do seed, com um `GET /users/<id>` por conta.
- **Recomendação:** `werkzeug.security.generate_password_hash`/`check_password_hash` (scrypt/pbkdf2 com salt), nunca serializar `password`, rehash no próximo login ou migração; elevar o tamanho mínimo de senha.

### [HIGH] Ausência de autenticação/autorização, token falso e escalonamento de papel
- **Local:** `routes/user_routes.py:210`, `routes/user_routes.py:52`, `routes/user_routes.py:71-72`, `routes/user_routes.py:119-122`, `routes/user_routes.py:134-151`
- **Evidência:** login retorna `'token': 'fake-jwt-token-' + str(user.id)` (`:210`) e nenhuma rota verifica token ou papel; `POST /users` aceita `role` do corpo, incluindo `admin` (`:52,71`); `PUT /users/<id>` permite trocar `role` e `active` de qualquer usuário (`:119-125`); `DELETE /users/<id>` apaga usuário e todas as suas tasks (`:140-146`). `User.is_admin` existe mas nunca é usado (`models/user.py:34`).
- **Impacto:** Qualquer cliente cria contas admin, altera/desativa/apaga qualquer usuário e todas as tasks; o "token" é previsível e não protege nada.
- **Recomendação:** Autenticação real (token assinado com `SECRET_KEY` vinda de ambiente) via decorator/`before_request`, autorização por papel nas rotas de escrita de usuários e categorias, e ignorar `role` no autocadastro.

### [HIGH] Regras de negócio e serialização dentro das rotas
- **Local:** `routes/task_routes.py:30-39`, `routes/task_routes.py:71-80`, `routes/task_routes.py:283-287`, `routes/user_routes.py:171-180`, `routes/report_routes.py:33-43`, `routes/report_routes.py:132-135`, `routes/report_routes.py:12-101`, `routes/task_routes.py:17-28`, `routes/user_routes.py:162-169`
- **Evidência:** a regra "atrasada = `due_date` passado e status não `done`/`cancelled`" está copiada em 6 handlers, enquanto `Task.is_overdue()` (`models/task.py:50-60`) implementa a mesma regra e não é usado. `get_tasks` e `get_user_tasks` remontam o dicionário da task à mão em vez de `to_dict()`. Relatórios (contagens, produtividade, taxas) são calculados inteiramente nos handlers.
- **Impacto:** Mudar a regra de atraso ou o formato da task exige editar vários arquivos; as respostas já divergem (`/users/<id>/tasks` omite `user_id`, `category_id`, `tags`, `updated_at`; `/tasks/search` e `/users/<id>` não trazem `overdue`).
- **Recomendação:** Services (`task_service`, `report_service`) com a regra de atraso única no model, serializador único da task, e rotas finas preservando os formatos atuais de cada endpoint.

### [HIGH] Configuração insegura de execução: debug, bind público e CORS aberto
- **Local:** `app.py:15`, `app.py:34`
- **Evidência:** `CORS(app)` sem restrição de origens; `app.run(debug=True, host='0.0.0.0', port=5000)`.
- **Impacto:** Debugger interativo do Werkzeug e tracebacks expostos na rede; qualquer site pode chamar a API a partir do navegador de um usuário, o que, somado à falta de autenticação, permite ações destrutivas cross-origin.
- **Recomendação:** `DEBUG`, host, porta e origens CORS vindos de ambiente com defaults seguros (`False`, `127.0.0.1`, lista vazia/explícita).

### [HIGH] Acoplamento rígido: config fixa, `create_all` no import e seed destrutivo
- **Local:** `app.py:9-16`, `app.py:30-31`, `seed.py:2`, `seed.py:11-14`
- **Evidência:** a aplicação é criada no nível do módulo com URI de banco fixa (`app.py:9-11`) e executa `db.create_all()` ao ser importada (`:30-31`); `seed.py` importa esse `app` e executa `Task/User/Category.query.delete()` no mesmo banco, sem confirmação nem checagem de ambiente.
- **Impacto:** Impossível apontar testes para um banco temporário sem editar o código; rodar `python seed.py` em um ambiente com dados reais apaga tudo.
- **Recomendação:** App factory `create_app(config)` com `DATABASE_URL` configurável, inicialização de schema explícita (comando CLI), seed acionado só por comando dedicado e com o banco configurado.

### [MEDIUM] Queries N+1
- **Local:** `routes/task_routes.py:41-57`, `routes/user_routes.py:22`, `routes/report_routes.py:55-56`, `routes/report_routes.py:161-163`, `routes/report_routes.py:15-28`
- **Evidência:** `User.query.get` e `Category.query.get` por task em `GET /tasks`; `len(u.tasks)` dispara lazy load por usuário em `GET /users`; `Task.query.filter_by(user_id=u.id)` por usuário no resumo; `count()` por categoria em `GET /categories`; 12 `count()` separados no início do resumo.
- **Impacto:** `GET /tasks` faz até 1 + 2N consultas; custo cresce linearmente com tasks/usuários/categorias (e nenhuma listagem é paginada).
- **Recomendação:** `joinedload`/`selectinload` para user/category, agregações com `func.count` + `group_by` para contagens por status, prioridade, usuário e categoria.

### [MEDIUM] Validação duplicada e inconsistente
- **Local:** `routes/task_routes.py:92-144` vs `routes/task_routes.py:166-213`; `utils/helpers.py:57-108`; `models/task.py:38-48`; `routes/user_routes.py:61-72` vs `routes/user_routes.py:102-125`; `routes/report_routes.py:173-180` vs `routes/report_routes.py:197-202`
- **Evidência:** a validação de task existe três vezes (create, update e `process_task_data`, que nunca é chamado) e `Task.validate_status/validate_priority` também não são usados; `update_task` não aceita título vazio da mesma forma que `create_task`; `update_user` não valida `name` (aceita vazio/`null`) nem o tipo de `active`; categorias não validam `color` em nenhum caminho (`is_valid_color` existe sem uso, `utils/helpers.py:52`); `update_category` não exige `name`. Constantes `VALID_STATUSES`/`VALID_ROLES` (`utils/helpers.py:110-111`) não são usadas pelas rotas, que repetem as listas literais.
- **Impacto:** Regras diferentes conforme o endpoint; dados inválidos entram pelo `PUT` (nome vazio, `active` string, cor arbitrária).
- **Recomendação:** Schemas compartilhados por entidade (o `marshmallow` já declarado serve), usados em create e update com `partial=True`.

### [MEDIUM] Falta de validação de tipos na fronteira (erros de cliente viram 500)
- **Local:** `routes/task_routes.py:96`, `routes/task_routes.py:113`, `routes/task_routes.py:167`, `routes/task_routes.py:182`, `routes/task_routes.py:261`, `routes/task_routes.py:264`, `routes/report_routes.py:196-197`
- **Evidência:** `priority` string (`"2"`) em `POST`/`PUT /tasks` → `TypeError` na comparação `< 1`; `title` numérico → `TypeError` em `len()`; `GET /tasks/search?priority=abc` → `ValueError` em `int()`; `PUT /categories/<id>` sem corpo JSON → `'name' in None` → `TypeError`. Nenhum desses caminhos tem `try`, então o Flask responde 500 (com traceback no navegador em modo debug).
- **Impacto:** Entradas malformadas simples geram 500 e expõem detalhes internos com `debug=True`.
- **Recomendação:** Validação de tipo antes das regras, com `400` e mensagem consistente.

### [MEDIUM] Tratamento de erro opaco com `except:` genérico
- **Local:** `routes/task_routes.py:62`, `routes/task_routes.py:137`, `routes/task_routes.py:204`, `routes/task_routes.py:236`, `routes/user_routes.py:130`, `routes/user_routes.py:149`, `routes/report_routes.py:186`, `routes/report_routes.py:207`, `routes/report_routes.py:221`, `utils/helpers.py:46`, `utils/helpers.py:49`, `utils/helpers.py:88`
- **Evidência:** blocos `except:` sem classe engolem qualquer exceção (inclusive `KeyboardInterrupt`/`SystemExit`); `get_tasks` envolve o handler inteiro e devolve só `'Erro interno'` sem log.
- **Impacto:** Falhas reais de banco ou bugs ficam invisíveis; não há log para diagnóstico.
- **Recomendação:** Capturar exceções específicas (`ValueError`, `SQLAlchemyError`), `@app.errorhandler` centralizado e log com `logging`.

### [MEDIUM] Exclusão de categoria deixa referências órfãs
- **Local:** `routes/report_routes.py:211-223`, `models/task.py:14`, `models/task.py:21`
- **Evidência:** `delete_category` remove a categoria sem tratar as tasks; o relacionamento é `backref='tasks'` sem `cascade` nem `ondelete`, e SQLite não aplica FKs sem `PRAGMA foreign_keys=ON`.
- **Impacto:** Tasks mantêm `category_id` de categoria inexistente; `GET /tasks` passa a devolver `category_name: null` com `category_id` preenchido.
- **Recomendação:** Definir política explícita (zerar `category_id` das tasks na mesma transação, ou bloquear a exclusão com `409` se houver tasks) e habilitar FKs no SQLite.

### [MEDIUM] APIs deprecated/legadas em uso
- **Local:** `datetime.utcnow()` em `models/task.py:15,16,52`, `models/user.py:14`, `models/category.py:11`, `routes/task_routes.py:31,72,215,285`, `routes/user_routes.py:172`, `routes/report_routes.py:35,42,45,71,133`, `services/notification_service.py:35`, `utils/helpers.py:38`, `seed.py:66,67,69,70,74`; `Query.get()` em `routes/task_routes.py:42,51,67,117,122,158,188,195,227`, `routes/user_routes.py:29,94,136,155`, `routes/report_routes.py:105,192,213`
- **Evidência:** `datetime.utcnow()` é deprecated desde o Python 3.12 (documentação oficial de `datetime`; emite `DeprecationWarning`). `Query.get()` é marcado como legado no SQLAlchemy 2.0 (emite `LegacyAPIWarning`); `flask-sqlalchemy==3.1.1` exige SQLAlchemy 2.x.
- **Impacto:** Warnings em runtime e risco de quebra em versões futuras; `utcnow()` produz datetimes *naive*, fáceis de comparar errado com datetimes com timezone.
- **Recomendação:** `datetime.now(timezone.utc)` (ou função `utcnow()` local que preserve o formato atual das respostas) e `db.session.get(Model, id)` / `db.get_or_404`. A troca para datetimes *aware* muda `str()` das datas e deve ser feita com teste de contrato.

### [LOW] Código morto e imports não usados
- **Local:** `app.py:7` (`os`, `sys`, `json`), `routes/task_routes.py:7` (`json`, `os`, `sys`, `time`), `routes/user_routes.py:6` (`hashlib`, `json`), `routes/report_routes.py:7-8` (`format_date`, `calculate_percentage`, `json`), `models/task.py:3` (`json`), `utils/helpers.py:3-7` (`os`, `json`, `sys`, `math`, `hashlib`); `services/notification_service.py` inteiro sem consumidor; em `utils/helpers.py`, `validate_email`, `sanitize_string`, `generate_id`, `log_action`, `parse_date`, `is_valid_color`, `process_task_data` e as constantes (`:110-116`) sem uso; `Task.validate_status`, `Task.validate_priority`, `Task.is_overdue`, `User.is_admin` sem uso; dependências `marshmallow`, `requests`, `python-dotenv` não importadas.
- **Recomendação:** Remover ou passar a usar (preferível para `is_overdue`, constantes e validações) durante a refatoração.

### [LOW] Magic strings/números repetidos
- **Local:** `routes/task_routes.py:110,177` (lista de status), `routes/task_routes.py:113,182` (`1`/`5`), `routes/task_routes.py:96-100,167-170` (`3`/`200`), `routes/user_routes.py:64,115` (`4`), `routes/user_routes.py:71,120` (lista de roles), `routes/report_routes.py:24-28,84-88,129` (prioridades `1..5`/`<= 2` mapeadas para nomes)
- **Recomendação:** Usar constantes/enums únicos de domínio (já esboçados em `utils/helpers.py:110-116`).

### [LOW] Logging via `print`
- **Local:** `routes/task_routes.py:149,153,219,234`, `routes/user_routes.py:83,89,147`, `services/notification_service.py:21,24`, `utils/helpers.py:39,41`
- **Evidência:** `print(f"ERRO: {str(e)}")`, `print(f"Usuário criado: {user.id} - {user.name}")`.
- **Recomendação:** `logging` com níveis; não registrar dados pessoais.

## APIs deprecated
Ver achado **[MEDIUM] APIs deprecated/legadas em uso**: `datetime.utcnow()` (deprecated no Python 3.12+) e `Query.get()` (legado no SQLAlchemy 2.0, usado via Flask-SQLAlchemy 3.1). Demais APIs do Flask 3.0 usadas (`Blueprint`, `route`, `request.get_json`, `jsonify`, retorno de `dict`) são atuais. Não foi executado `pip-audit`; nenhuma CVE é alegada para as versões fixadas.

## Gate da Fase 2
A auditoria não alterou o código-alvo. Aprovar a Fase 3? (sim/não)
