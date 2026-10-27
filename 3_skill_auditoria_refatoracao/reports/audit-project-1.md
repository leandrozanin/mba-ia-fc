# Relatório de Auditoria — code-smells-project

## Análise do projeto
- **Linguagem/framework:** Python 3.12.10 (`.venv/pyvenv.cfg`) com Flask 3.1.1 e flask-cors 5.0.1 (`requirements.txt`, ambos instalados na `.venv`). A aplicação é criada em `app.py:6` (`Flask(__name__)`) e as rotas são registradas com `app.add_url_rule` (`app.py:11-30`) e `@app.route` (`app.py:32`, `47`, `59`).
- **Banco e dependências relevantes:** SQLite pelo módulo `sqlite3` da biblioteca padrão. O caminho fixo é `loja.db` (`database.py:5`). O schema é criado e populado com dados de exemplo em tempo de execução (`database.py:14-84`). Não há ORM nem migrations.
- **Domínio:** API de e-commerce ("API da Loja") com produtos, usuários/login, pedidos com itens e baixa de estoque, relatório de vendas e endpoints administrativos.
- **Arquitetura atual:** MVC parcial e plano. `app.py` cuida do bootstrap e do registro de rotas, mas também tem handlers administrativos com SQL direto. `controllers.py` reúne handlers HTTP, validação, "notificações" via `print` e o health check com SQL direto. `models.py` concentra a persistência de todos os domínios, com regras de negócio (workflow de pedido, faixas de desconto). `database.py` mantém uma conexão global única e faz o schema e o seed. Fluxo: rota (`app.py`) → função em `controllers.py` → função em `models.py` → `get_db()` global → `jsonify`. Não há camada de serviço, autenticação, middleware nem error handlers.
- **Arquivos-fonte analisados / excluídos:** 4 arquivos Python analisados (`app.py` com 88 linhas, `controllers.py` com 292, `database.py` com 86, `models.py` com 314; 780 linhas no total), além de `requirements.txt` e `README.md`. Ficaram de fora `.venv/` (dependências instaladas) e `.claude/` (a própria skill). Não existe `loja.db` no diretório: ele só é criado no primeiro boot.
- **Comandos de teste e boot disponíveis:** não há testes no projeto (nenhum arquivo `test_*`, `tests/`, pytest ou configuração de testes). Boot pelo `README.md`: `pip install -r requirements.txt` e depois `python app.py`, que sobe em `0.0.0.0:5000` com `debug=True` (`app.py:88`).
- **Endpoints registrados:**
  - `GET /`
  - `GET /health`
  - `GET /produtos`, `GET /produtos/busca`, `GET /produtos/<int:id>`, `POST /produtos`, `PUT /produtos/<int:id>`, `DELETE /produtos/<int:id>`
  - `GET /usuarios`, `GET /usuarios/<int:id>`, `POST /usuarios`, `POST /login`
  - `POST /pedidos`, `GET /pedidos`, `GET /pedidos/usuario/<int:usuario_id>`, `PUT /pedidos/<int:pedido_id>/status`
  - `GET /relatorios/vendas`
  - `POST /admin/reset-db`, `POST /admin/query`

> Esta auditoria foi feita por análise estática. A aplicação não foi executada e nenhum payload foi enviado, para não criar `loja.db` nem alterar estado antes da aprovação.

## Resumo
| Severidade | Quantidade |
|---|---:|
| CRITICAL | 4 |
| HIGH | 5 |
| MEDIUM | 4 |
| LOW | 4 |
| **Total** | **17** |

> **Nota de revisão:** a execução da skill registrou HIGH = 6 e Total = 18 nesta tabela, mas o relatório contém 5 blocos HIGH (17 achados). A contagem foi corrigida, e o template de relatório da skill ganhou uma regra de conferência do resumo.

## Achados

### [CRITICAL] SQL injection em quase todas as queries de `models.py`
- **Local:** `models.py:28`, `models.py:47-50`, `models.py:57-61`, `models.py:68`, `models.py:92`, `models.py:109-111`, `models.py:126-129`, `models.py:140`, `models.py:148-151`, `models.py:155-166`, `models.py:174`, `models.py:279-281`, `models.py:289-299`
- **Evidência:** as queries são montadas concatenando entrada do usuário, por exemplo `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` (`models.py:110`) e `" AND (nome LIKE '%" + termo + "%' ..."` (`models.py:291`). Nenhuma query de `models.py` usa parâmetros `?`.
- **Descrição:** `email` e `senha` do `POST /login`, `nome`/`descricao`/`categoria` de produtos, `nome`/`email`/`senha` de usuários e `q`/`categoria` da busca vão direto para o SQL. Os campos numéricos passam por `str()`, mas nunca são validados como número (por exemplo, `item["produto_id"]` em `models.py:140`).
- **Impacto:** é possível entrar sem senha (um email como `' OR '1'='1' --` faz a query devolver o primeiro usuário, o seed `Admin`), extrair dados de outras tabelas via `UNION` na busca e corromper registros por `POST/PUT /produtos` e `POST /usuarios`. Um nome com apóstrofo legítimo (ex.: `D'Ávila`) também quebra a query e devolve 500.
- **Recomendação:** usar placeholders `?` com tupla de parâmetros em todas as queries e montar os filtros dinâmicos da busca com uma lista de cláusulas fixas mais a lista de parâmetros.

### [CRITICAL] Endpoints administrativos sem autenticação: execução arbitrária de SQL e reset do banco
- **Local:** `app.py:59-78` (`POST /admin/query`), `app.py:47-57` (`POST /admin/reset-db`)
- **Evidência:** `query = dados.get("sql", "")` seguido de `cursor.execute(query)` e `db.commit()` (`app.py:62`, `69`, `75`). O reset executa `DELETE FROM` em todas as tabelas (`app.py:51-55`). Nenhuma das duas rotas checa identidade ou permissão.
- **Descrição:** qualquer cliente HTTP consegue rodar SQL arbitrário (SELECT, UPDATE, DELETE, DROP) ou apagar o banco inteiro.
- **Impacto:** leitura, alteração e destruição total dos dados (inclusive das senhas). Com `CORS(app)` aberto (`app.py:9`), o ataque pode partir até de uma página web de terceiros.
- **Recomendação:** remover `/admin/query`. Se o reset for necessário para desenvolvimento, deixá-lo atrás de flag de ambiente desabilitada por padrão e de autenticação/autorização de administrador.

### [CRITICAL] Segredo embutido no código e exposto pelo `/health`
- **Local:** `app.py:7` (`SECRET_KEY` fixa), `controllers.py:289` (o mesmo valor devolvido na resposta), `controllers.py:285-288`
- **Evidência:** `app.config["SECRET_KEY"]` recebe um literal versionado, e `health_check` devolve no JSON a chave `secret_key` com esse mesmo literal, junto com `db_path`, `debug` e `ambiente`. Os valores ficam de fora deste relatório de propósito.
- **Descrição:** a chave de assinatura do Flask está no repositório e qualquer pessoa pode lê-la em um endpoint público.
- **Impacto:** quem tem a chave consegue forjar cookies de sessão assinados pelo Flask. O endpoint também expõe metadados operacionais (caminho do banco, modo debug).
- **Recomendação:** ler `SECRET_KEY` de variável de ambiente ou secret store, sem default inseguro em produção, e rotacionar o valor atual. Reduzir o `/health` a status/conectividade, sem configuração nem segredos.

### [CRITICAL] Senhas em texto puro, devolvidas pela API
- **Local:** `models.py:83` e `models.py:99` (campo `senha` na serialização), `models.py:126-129` (gravação sem hash), `models.py:110` (comparação em texto puro), `database.py:31` e `database.py:76-78` (coluna e seed com senhas literais)
- **Evidência:** `get_todos_usuarios` e `get_usuario_por_id` incluem `"senha": row["senha"]`, e `GET /usuarios` e `GET /usuarios/<id>` (`controllers.py:128-144`) devolvem isso sem filtro nem autenticação.
- **Descrição:** a senha é guardada como chegou no request e entregue a qualquer cliente que liste usuários. O seed versiona credenciais, inclusive de uma conta `admin`.
- **Impacto:** qualquer pessoa obtém as credenciais de todos os usuários, inclusive do administrador. Vaza também a senha de quem reutiliza a mesma senha em outros serviços.
- **Recomendação:** guardar só hash com salt (`werkzeug.security.generate_password_hash`/`check_password_hash`, já disponível pelo Flask), remover `senha` de toda serialização e tirar as credenciais fixas do seed (ou gerá-las fora do código, só em desenvolvimento).

### [HIGH] Ausência de autenticação/autorização nas rotas de dados
- **Local:** `app.py:18-28`, `controllers.py:167-183`
- **Evidência:** o `POST /login` devolve os dados do usuário (`controllers.py:180`), mas não emite sessão, token nem cookie. Nenhuma rota verifica identidade, e o campo `tipo` (`admin`/`cliente`) nunca é consultado.
- **Descrição:** listagem de usuários, todos os pedidos, pedidos de qualquer usuário, mudança de status de pedido, CRUD de produtos e relatório de vendas ficam abertos a qualquer cliente.
- **Impacto:** qualquer pessoa altera preços e estoque, apaga produtos, aprova ou cancela pedidos alheios e lê dados pessoais e financeiros.
- **Recomendação:** implementar autenticação (sessão Flask ou token) emitida no login e autorização por papel (`admin` para CRUD de produtos, relatórios e status; o dono para os próprios pedidos), centralizada em decorator ou middleware.

### [HIGH] Modo debug ligado e servidor exposto em todas as interfaces, com CORS irrestrito
- **Local:** `app.py:8`, `app.py:88`, `app.py:9`
- **Evidência:** `app.config["DEBUG"] = True` e `app.run(host="0.0.0.0", port=5000, debug=True)`; `CORS(app)` sem restrição de origem.
- **Descrição:** o debugger interativo do Werkzeug fica ativo e acessível pela rede. O `/health` ainda se anuncia como `"ambiente": "producao"` (`controllers.py:286`).
- **Impacto:** o debugger do Werkzeug executa código Python arbitrário no console de erro (protegido só por PIN). Stack traces vazam código e caminhos. CORS aberto permite que qualquer site chame a API a partir do navegador da vítima.
- **Recomendação:** ler debug, host e origens CORS de configuração por ambiente, com padrão seguro (`debug=False`, origens explícitas), e usar um servidor WSGI de produção.

### [HIGH] Workflow de pedido sem controle transacional e com corrida de estoque
- **Local:** `models.py:133-169`, `database.py:10`, `controllers.py:245-250`
- **Evidência:** a função checa o estoque num primeiro loop (`models.py:139-146`) e depois faz INSERT do pedido, INSERT dos itens e UPDATE do estoque (`models.py:148-166`), com um único `commit()` no final e nenhum `rollback()`. A conexão é global e compartilhada entre threads (`check_same_thread=False`).
- **Descrição:** se der exceção depois do INSERT do pedido (por exemplo, um item sem a chave `quantidade` faz `models.py:144` falhar só depois de itens anteriores terem sido processados no segundo loop, ou um erro de SQL), as escritas pendentes não são revertidas. Elas continuam na conexão compartilhada e são gravadas pelo próximo `commit()` de qualquer outra requisição. A checagem de estoque e a baixa também não são atômicas entre requisições concorrentes. Por fim, mudar o status para `cancelado` só imprime "Devolver estoque" (`controllers.py:250`) e não devolve nada.
- **Impacto:** pedidos órfãos ou parciais, estoque negativo (venda acima do estoque) e estoque que não volta em cancelamentos.
- **Recomendação:** pôr o workflow numa transação explícita (`with conn:` ou `BEGIN IMMEDIATE` com rollback em exceção), fazer a baixa condicional (`UPDATE ... SET estoque = estoque - ? WHERE id = ? AND estoque >= ?`, conferindo `rowcount`), implementar a devolução de estoque no cancelamento e cobrir os casos de falha intermediária com testes.

### [HIGH] Conexão SQLite global e mutável compartilhada entre threads
- **Local:** `database.py:4-11`, `database.py:86`
- **Evidência:** `db_connection = None` em escopo de módulo, `global db_connection` e `sqlite3.connect(db_path, check_same_thread=False)`; o caminho `db_path = "loja.db"` é fixo.
- **Descrição:** todas as requisições, em qualquer thread, usam a mesma conexão e o mesmo estado transacional. Não há ciclo de vida por request, não há fechamento e o caminho do banco não é configurável. Criação de schema e seed acontecem como efeito colateral do primeiro `get_db()`.
- **Impacto:** transações de requisições diferentes se misturam (o commit de uma grava as escritas pendentes da outra), há risco de erros de concorrência no SQLite e os testes não conseguem isolar o banco (não dá para apontar para um arquivo temporário).
- **Recomendação:** usar uma conexão por request (`flask.g` mais `teardown_appcontext`), ler o caminho do banco da configuração do app (app factory) e separar a inicialização do schema e do seed num passo explícito.

### [HIGH] Persistência na camada de apresentação e regras de negócio espalhadas
- **Local:** `app.py:49-55`, `app.py:66-76`, `controllers.py:266-274`, `models.py:256-262`, `controllers.py:208-210`, `controllers.py:247-250`
- **Evidência:** handlers em `app.py` e o `health_check` em `controllers.py` chamam `get_db()` e `cursor.execute` direto. A regra de desconto por faixa de faturamento fica em `models.py` (camada de dados), e os efeitos de domínio (e-mail, SMS, push, preparar envio, devolver estoque) são `print`s dentro dos controllers.
- **Descrição:** as responsabilidades não seguem as camadas: rotas acessam o driver, a camada de dados decide regra comercial e os controllers simulam integrações.
- **Impacto:** fica difícil testar regras isoladamente, mudanças de regra comercial mexem na camada de acesso a dados, e as notificações nunca acontecem de fato, mesmo com a resposta da API dizendo que deu certo.
- **Recomendação:** criar uma camada de serviços/aplicação (pedido, relatório, notificações) entre controllers e repositórios, tirar todo SQL de `app.py` e `controllers.py`, e trocar as notificações por uma interface de notificador injetável.

### [MEDIUM] Queries N+1 na listagem de pedidos
- **Local:** `models.py:187-199`, `models.py:219-231`
- **Evidência:** para cada pedido roda um `SELECT * FROM itens_pedido WHERE pedido_id = ...` e, para cada item, um `SELECT nome FROM produtos WHERE id = ...`.
- **Descrição:** `GET /pedidos` e `GET /pedidos/usuario/<id>` executam 1 + P + I queries (P pedidos, I itens). As duas funções também são cópias quase idênticas.
- **Impacto:** a latência cresce linearmente com o volume de pedidos e itens, e a lógica duplicada pode divergir.
- **Recomendação:** uma query com `JOIN` entre `pedidos`, `itens_pedido` e `produtos` (ou uma em lote por `pedido_id IN (...)`) agrupada em memória, numa função única com filtro opcional por usuário.

### [MEDIUM] Validação ausente ou de tipo imprevisível na fronteira HTTP
- **Local:** `controllers.py:43-46`, `controllers.py:118-121`, `controllers.py:169-170`, `controllers.py:239-240`, `controllers.py:195-201` com `models.py:139-146`, `controllers.py:153-158` com `database.py:27-34`, `controllers.py:245` com `models.py:279-283`
- **Evidência:**
  - `preco < 0` com `preco` string gera `TypeError` e devolve 500, não 400.
  - `float(preco_min)` com valor inválido gera `ValueError` e devolve 500.
  - `dados.get(...)` com body ausente ou não-JSON falha em `login` e `atualizar_status_pedido` (500).
  - Os itens do pedido não são validados: uma `quantidade` negativa passa na checagem `estoque < quantidade`, aumenta o estoque e gera um total negativo; `quantidade` ausente gera `KeyError`.
  - O e-mail de usuário não tem formato validado nem unicidade (sem `UNIQUE` no schema).
  - Atualizar o status de um pedido inexistente devolve 200 "Status atualizado".
- **Descrição:** tipos, limites e existência de recursos não são checados de forma previsível antes de chegar à regra de negócio ou ao SQL.
- **Impacto:** erros 500 em entradas comuns, manipulação de estoque e de total com quantidades negativas, usuários duplicados e respostas de sucesso falsas.
- **Recomendação:** validar na fronteira com schema/validador (tipos numéricos, `quantidade > 0`, `produto_id` inteiro, e-mail, body JSON obrigatório), devolver 400/404 coerentes, adicionar `UNIQUE(email)` e checar `rowcount` nas atualizações.

### [MEDIUM] Validação de produto duplicada e inconsistente entre criação e atualização
- **Local:** `controllers.py:28-54` (create) e `controllers.py:72-90` (update)
- **Evidência:** o create valida tamanho do nome (`controllers.py:47-50`) e a lista de categorias válidas (`controllers.py:52-54`). O update copia as checagens de presença e de sinal, mas não valida tamanho do nome nem categoria.
- **Descrição:** a mesma regra está copiada e já divergiu.
- **Impacto:** um `PUT /produtos/<id>` aceita nome vazio ou de 1 caractere e categorias fora da lista, deixando dados inválidos que o `POST` rejeitaria.
- **Recomendação:** um validador de produto compartilhado, usado pelo create e pelo update, com mensagens de erro coerentes.

### [MEDIUM] Tratamento de erro opaco que expõe exceções internas
- **Local:** `controllers.py:10-12` e todos os outros `except Exception as e` de `controllers.py` (linhas 21, 60, 95, 108, 125, 133, 143, 164, 185, 218, 226, 234, 254, 261, 291), além de `app.py:77-78`
- **Evidência:** `return jsonify({"erro": str(e)}), 500` em todos os handlers.
- **Descrição:** qualquer exceção, de validação ou de banco, vira 500 com a mensagem interna crua no corpo da resposta. Não há log estruturado nem distinção entre erro esperado e inesperado.
- **Impacto:** as respostas vazam mensagens do SQLite (o que facilita explorar o SQL injection acima), erros de cliente aparecem como erro de servidor e não sobra rastro útil para diagnóstico.
- **Recomendação:** exceções de domínio específicas mapeadas para 4xx, um `errorhandler` global que registre a exceção com `logging` e devolva mensagem genérica no 500, e a remoção dos `try/except` repetidos em cada handler.

### [LOW] Logging improvisado com `print` e dados pessoais nos logs
- **Local:** `controllers.py:8`, `11`, `57`, `61`, `106`, `161`, `179`, `182`, `208-210`, `219`, `248`, `250`; `app.py:56`, `app.py:83-86`
- **Evidência:** `print("Usuário criado: " + email)`, `print("Login bem-sucedido: " + email)`, `print("Login falhou: " + email)`.
- **Descrição:** os logs vão para stdout sem nível nem estrutura e incluem e-mails (dado pessoal) em tentativas de login.
- **Impacto:** observabilidade ruim, dado pessoal em log e mensagens que parecem integrações reais ("ENVIANDO EMAIL") mas não fazem nada.
- **Recomendação:** usar `logging` com níveis, sem payload sensível (no máximo um ID do usuário), e remover os prints de notificação simulada.

### [LOW] Magic numbers/strings sem nome de domínio
- **Local:** `controllers.py:52` (categorias), `controllers.py:242` e `models.py:247-253` (status de pedido), `models.py:257-262` (faixas e percentuais de desconto), `controllers.py:47-50` (limites de nome), `app.py:36` e `controllers.py:285` (versão `"1.0.0"` duplicada), `controllers.py:286-288` (ambiente/caminho/debug fixos na resposta)
- **Evidência:** listas e números literais repetidos ou embutidos na lógica.
- **Descrição:** estados, categorias e limiares não têm uma fonte única.
- **Impacto:** é fácil esquecer um lugar ao mudar uma regra (o caso da categoria no update já aconteceu), e o `/health` informa dados que não correspondem à configuração real.
- **Recomendação:** constantes ou enums de domínio (`CATEGORIAS_VALIDAS`, `StatusPedido`, `FAIXAS_DESCONTO`, `APP_VERSION`) num módulo único, e valores do `/health` tirados da configuração.

### [LOW] Código morto, imports não usados e consultas redundantes
- **Local:** `database.py:2` (`import os` sem uso), `models.py:2` (`import sqlite3` sem uso), `controllers.py:268` (`SELECT 1` cujo resultado é descartado), `models.py:155-156` (relê o preço já lido em `models.py:140-146`), `controllers.py:200` (`not itens or len(itens) == 0`, redundante)
- **Evidência:** símbolos e consultas sem efeito no resultado.
- **Descrição:** sobras que aumentam o ruído e o número de idas ao banco.
- **Impacto:** manutenção mais difícil e queries extras por item de pedido.
- **Recomendação:** remover os imports e as consultas sem efeito, e reaproveitar o preço lido na validação ao gravar `itens_pedido`.

### [LOW] Mapeamento de linhas duplicado e nomes que sombreiam builtins
- **Local:** `models.py:12-21`, `models.py:31-40`, `models.py:304-313` (mapeamento de produto repetido); `models.py:79-86` e `models.py:95-102` (usuário); `controllers.py:14`, `24`, `56`, `64`, `98`, `136`, `160` e `models.py:24`, `54`, `65`, `89` (variável/parâmetro `id`)
- **Evidência:** o mesmo dicionário de serialização copiado em várias funções; `id` como nome de parâmetro e de variável local.
- **Descrição:** a serialização é duplicada, então um campo novo ou removido (como tirar `senha`) precisa ser alterado em vários pontos. `id` sombreia o builtin.
- **Impacto:** risco de divergência entre endpoints e leitura menos clara.
- **Recomendação:** funções `produto_from_row`/`usuario_publico_from_row` únicas e nomes como `produto_id`/`usuario_id`.

## APIs deprecated
Nenhuma identificada. Conferi:
- **Flask 3.1.1:** `Flask(...)`, `app.config`, `add_url_rule`, `route`, `jsonify`, `request.get_json`, `request.args` e `app.run` são APIs atuais, sem uso de `flask.json.JSONEncoder`, `before_first_request` ou `_app_ctx_stack`, que foram removidos no 2.3/3.0.
- **flask-cors 5.0.1:** só `CORS(app)`.
- **`sqlite3` no Python 3.12:** os adaptadores/conversores padrão de `datetime`, deprecated desde o 3.12, não são usados (não há `detect_types` nem parâmetros `datetime`). `datetime.utcnow()` não aparece no código.

## Gate da Fase 2
A auditoria não alterou o código-alvo: o único arquivo criado foi este `audit-report.md`. Aprovar a Fase 3 (refatoração MVC)? (sim/não)
