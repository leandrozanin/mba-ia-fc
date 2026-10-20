# Relatório de Auditoria — code-smells-project

## Análise do projeto
- **Linguagem/framework:** Python / Flask. Evidência: `app.py:1,6` (`from flask import Flask` / `Flask(__name__)`), rotas registradas via `app.add_url_rule` (`app.py:11-30`) e `@app.route` (`app.py:32,47,59`). Dependências declaradas em `requirements.txt`: `flask==3.1.1`, `flask-cors==5.0.1`.
- **Banco e dependências relevantes:** SQLite via `sqlite3` da stdlib (`database.py:1,10`), arquivo `loja.db` relativo ao diretório de execução (`database.py:5`). Schema (4 tabelas: `produtos`, `usuarios`, `pedidos`, `itens_pedido`) e seed criados em runtime dentro de `get_db()` (`database.py:14-84`). Sem ORM, sem migrations. CORS global via `flask_cors.CORS(app)` (`app.py:9`).
- **Domínio:** API de e-commerce — catálogo de produtos (CRUD + busca), usuários (cadastro/login), pedidos (criação com baixa de estoque, listagem, mudança de status) e relatório de vendas.
- **Arquitetura atual:** MVC parcial / monólito em 4 módulos planos. Fluxo de requisição:
  ```
  app.py (config + registro de rotas + 2 handlers admin com SQL inline)
     └─> controllers.py (parse HTTP + validação + regras + "notificações" via print)
            └─> models.py (SQL concatenado + serialização + regras: pedido, desconto)
                   └─> database.py (conexão global única + DDL + seed)
  ```
  Não há camada de serviço, schemas de validação, app factory, Blueprints, autenticação nem tratamento centralizado de erros. Persistência também ocorre fora de `models.py` (`app.py:49-55,66-76`, `controllers.py:266-274`).
- **Arquivos-fonte analisados / excluídos:** 4 arquivos Python analisados integralmente — `app.py` (88 linhas), `controllers.py` (292), `models.py` (314), `database.py` (86) — total ≈ 780 linhas; mais `requirements.txt` e `README.md`. Excluídos: nenhum (não há `.venv`, caches, builds ou `loja.db` versionados no diretório).
- **Comandos de teste e boot disponíveis:** boot `pip install -r requirements.txt && python app.py` (README; `app.py:80-88`, sobe em `0.0.0.0:5000` com `debug=True`). **Não há testes** no projeto. Limitação: nesta fase a aplicação não foi executada; a análise é estática.

### Endpoints (a partir do registro real de rotas em `app.py`)
| Método | Rota | Handler |
|---|---|---|
| GET | `/` | `app.index` |
| GET | `/produtos` | `listar_produtos` |
| GET | `/produtos/busca` | `buscar_produtos` (`q`, `categoria`, `preco_min`, `preco_max`) |
| GET | `/produtos/<int:id>` | `buscar_produto` |
| POST | `/produtos` | `criar_produto` |
| PUT | `/produtos/<int:id>` | `atualizar_produto` |
| DELETE | `/produtos/<int:id>` | `deletar_produto` |
| GET | `/usuarios` | `listar_usuarios` |
| GET | `/usuarios/<int:id>` | `buscar_usuario` |
| POST | `/usuarios` | `criar_usuario` |
| POST | `/login` | `login` |
| POST | `/pedidos` | `criar_pedido` |
| GET | `/pedidos` | `listar_todos_pedidos` |
| GET | `/pedidos/usuario/<int:usuario_id>` | `listar_pedidos_usuario` |
| PUT | `/pedidos/<int:pedido_id>/status` | `atualizar_status_pedido` |
| GET | `/relatorios/vendas` | `relatorio_vendas` |
| GET | `/health` | `health_check` |
| POST | `/admin/reset-db` | `app.reset_database` |
| POST | `/admin/query` | `app.executar_query` |

## Resumo
| Severidade | Quantidade |
|---|---:|
| CRITICAL | 4 |
| HIGH | 5 |
| MEDIUM | 5 |
| LOW | 3 |
| **Total** | **17** |

## Achados

### [CRITICAL] SQL injection em praticamente todas as queries
- **Local:** `models.py:28`, `models.py:47-50`, `models.py:57-61`, `models.py:68`, `models.py:92`, `models.py:109-111`, `models.py:126-129`, `models.py:140`, `models.py:148-151`, `models.py:155-166`, `models.py:174`, `models.py:188`, `models.py:192`, `models.py:279-281`, `models.py:289-299`
- **Evidência:** `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` (`models.py:110`); `" AND (nome LIKE '%" + termo + "%' ..."` (`models.py:291`); `"INSERT INTO produtos ... VALUES ('" + nome + "', '" + descricao + "', " + str(preco) ...` (`models.py:48-49`).
- **Descrição:** Entradas do corpo JSON e da query string são concatenadas diretamente no SQL. Só o seed (`database.py:70-83`) usa parâmetros `?`.
- **Impacto:** Bypass de autenticação em `POST /login` (ex.: `email` com `' OR '1'='1' --`), leitura/alteração arbitrária de dados via `GET /produtos/busca?q=...`, e quebra de queries com nomes que contenham apóstrofo (ex.: produto `Monitor 27''` do próprio seed não poderia ser recriado via API). `preco`/`quantidade` não são validados como número, então também injetam em contexto numérico (`models.py:49,150,164`).
- **Recomendação:** Usar exclusivamente queries parametrizadas (`cursor.execute(sql, params)`) em todo o acesso a dados; montar filtros dinâmicos de busca com lista de cláusulas fixas + lista de parâmetros.

### [CRITICAL] Endpoints administrativos sem autenticação: SQL arbitrário e reset do banco
- **Local:** `app.py:47-57`, `app.py:59-78`
- **Evidência:** `POST /admin/query` executa `cursor.execute(query)` com `query = dados.get("sql", "")` vindo do cliente (`app.py:62,69`) e faz `commit` em não-SELECT (`app.py:75`); `POST /admin/reset-db` executa `DELETE` em todas as tabelas (`app.py:51-55`). Nenhuma verificação de identidade/papel em nenhuma rota.
- **Descrição:** Qualquer cliente de rede pode ler, alterar ou apagar todo o banco com uma requisição.
- **Impacto:** Comprometimento total de confidencialidade e integridade dos dados (inclusive senhas, ver próximo achado) e perda de dados irreversível.
- **Recomendação:** Remover `/admin/query`. Remover `/admin/reset-db` ou restringi-lo a ambiente de desenvolvimento/teste por configuração explícita (desligado por padrão).

### [CRITICAL] Segredo embutido e exposto publicamente
- **Local:** `app.py:7`, `controllers.py:285-289`
- **Evidência:** `SECRET_KEY` atribuída com literal fixo no código (`app.py:7`); o mesmo valor é devolvido no JSON de `GET /health` na chave `secret_key` (`controllers.py:289`), junto com `db_path`, `debug` e `ambiente` (`controllers.py:286-288`). Valor omitido neste relatório.
- **Descrição:** A chave de assinatura do Flask está versionada e é publicada por um endpoint sem autenticação.
- **Impacto:** Quem conhece a `SECRET_KEY` pode forjar cookies de sessão assinados pelo Flask; o health check ainda revela detalhes operacionais úteis para ataque.
- **Recomendação:** Ler `SECRET_KEY` de variável de ambiente (gerar valor aleatório em dev quando ausente), nunca retorná-la em respostas; reduzir `/health` a status e conectividade. Tratar a chave atual como comprometida.

### [CRITICAL] Senhas armazenadas em texto puro e expostas pela API
- **Local:** `database.py:31`, `database.py:75-79`, `models.py:83`, `models.py:99`, `models.py:109-111`, `models.py:126-129`
- **Evidência:** coluna `senha TEXT` gravada sem hash (`models.py:127-128`); login compara a senha em texto no SQL (`models.py:110`); `get_todos_usuarios` e `get_usuario_por_id` incluem `"senha": row["senha"]` (`models.py:83,99`), servidos por `GET /usuarios` e `GET /usuarios/<id>` sem autenticação. Seed cria contas, incluindo `admin`, com senhas fixas no código (`database.py:76-78`; valores omitidos).
- **Descrição:** Credenciais de todos os usuários ficam legíveis no banco e em endpoints públicos.
- **Impacto:** Qualquer pessoa obtém a senha de qualquer conta (inclusive admin) com um `GET`; vazamento do arquivo `loja.db` expõe todas as senhas.
- **Recomendação:** Armazenar hash com salt (ex.: `werkzeug.security.generate_password_hash`/`check_password_hash`, já disponível via Flask), nunca serializar o campo `senha`, e migrar senhas existentes para hash na inicialização. Seed com credenciais apenas para dev/teste.

### [HIGH] Configuração insegura de execução: debug ligado, bind em todas as interfaces e CORS aberto
- **Local:** `app.py:8`, `app.py:9`, `app.py:88`
- **Evidência:** `app.config["DEBUG"] = True`; `CORS(app)` sem restrição de origens; `app.run(host="0.0.0.0", port=5000, debug=True)`.
- **Descrição:** O servidor de desenvolvimento roda com debugger interativo do Werkzeug e fica acessível na rede; qualquer origem pode chamar a API pelo navegador.
- **Impacto:** Exposição de tracebacks e do console de depuração a clientes de rede; combinado com os endpoints admin, qualquer página web pode disparar requisições destrutivas a partir do navegador de quem acessa.
- **Recomendação:** Ler `DEBUG`, host, porta e origens CORS de variáveis de ambiente com defaults seguros (`debug=False`, `127.0.0.1`).

### [HIGH] Conexão SQLite global compartilhada entre threads, com schema e seed no acesso
- **Local:** `database.py:4-10`, `database.py:14-84`
- **Evidência:** `db_connection = None` global; `sqlite3.connect(db_path, check_same_thread=False)` reutilizada por todas as requisições; DDL e seed executados na primeira chamada a `get_db()`; `db_path` fixo `"loja.db"`.
- **Descrição:** Estado global mutável com uma única conexão/transação compartilhada; caminho do banco não configurável; não há fechamento por request nem por aplicação.
- **Impacto:** Com o servidor multi-thread do Flask, requisições concorrentes compartilham a mesma transação (um `commit` de uma requisição persiste escritas parciais de outra); impossível usar banco isolado em testes sem editar o código.
- **Recomendação:** App factory com `DATABASE` configurável; conexão por request em `flask.g` com `teardown_appcontext`; inicialização de schema/seed explícita e separada.

### [HIGH] Criação de pedido sem controle transacional e com corrida de estoque
- **Local:** `models.py:133-169`
- **Evidência:** valida estoque num loop (`models.py:139-146`), insere o pedido (`models.py:148-152`) e depois, em outro loop, insere itens e faz `UPDATE produtos SET estoque = estoque - <qtd>` (`models.py:154-166`) sem `try/rollback`; `commit` único no final (`models.py:168`). Os retornos de erro dos `models.py:143,145` saem sem `rollback`.
- **Descrição:** Uma exceção no segundo loop (ex.: item sem `quantidade`) deixa `INSERT`s pendentes na conexão compartilhada, que serão persistidos pelo próximo `commit` de qualquer outra requisição. O estoque é verificado e decrementado em momentos diferentes, sem guarda `estoque >= qtd` no `UPDATE`.
- **Impacto:** Pedidos órfãos/sem itens, estoque inconsistente e estoque negativo sob concorrência ou itens repetidos no mesmo pedido (ex.: dois itens do mesmo produto, cada um ≤ estoque, somando mais que o estoque).
- **Recomendação:** Executar o workflow em uma transação (`with conn:` / rollback em erro), agregar quantidades por produto antes de validar e usar `UPDATE ... WHERE id = ? AND estoque >= ?` verificando `rowcount`.

### [HIGH] Persistência fora da camada de modelo
- **Local:** `app.py:49-55`, `app.py:66-76`, `controllers.py:266-274`
- **Evidência:** handlers em `app.py` e `health_check` em `controllers.py` chamam `get_db()` e executam SQL diretamente.
- **Descrição:** A camada HTTP conhece o driver e o schema, ignorando `models.py`.
- **Impacto:** Regras de acesso a dados espalhadas; mudanças de schema exigem alterar rotas; impede testar controllers isoladamente.
- **Recomendação:** Mover as consultas de contagem/health para o model; deixar app/rotas apenas como adaptadores HTTP.

### [HIGH] Regras de negócio e efeitos colaterais misturados em controllers e models
- **Local:** `controllers.py:208-210`, `controllers.py:247-250`, `models.py:256-262`, `models.py:133-169`
- **Evidência:** "envio" de e-mail/SMS/push via `print` dentro do controller (`controllers.py:208-210`); ao cancelar, o controller apenas imprime "Devolver estoque" (`controllers.py:250`) sem devolver; faixas de desconto do relatório calculadas no model (`models.py:256-262`); workflow de pedido inteiro no model.
- **Descrição:** Não há camada de aplicação; regras de pedido, notificação e relatório ficam divididas entre HTTP e SQL. A regra anunciada de devolução de estoque no cancelamento não é implementada.
- **Impacto:** Comportamento de negócio difícil de testar e de evoluir; cancelamentos não restauram estoque; status pode ser alterado para pedido inexistente com resposta `200` (`models.py:279-283` não verifica `rowcount`).
- **Recomendação:** Extrair um serviço de pedidos/relatórios com as regras (criação, transição de status, desconto) e um notificador isolado; controllers só convertem HTTP ↔ chamadas de serviço.

### [MEDIUM] Falta de validação de entrada com efeitos em dados
- **Local:** `controllers.py:37-50`, `controllers.py:118-121`, `controllers.py:169-170`, `controllers.py:195-201`, `controllers.py:239-240`, `models.py:139-146`
- **Evidência:** `preco`/`estoque` não têm tipo verificado (`preco < 0` com string gera `TypeError` → 500); `float(preco_min)` inválido → 500; `login` e `atualizar_status_pedido` chamam `dados.get` sem checar corpo nulo (→ 500); itens de pedido sem validação de `produto_id`/`quantidade` (KeyError → 500) e `quantidade` zero/negativa é aceita — com quantidade negativa o `UPDATE estoque = estoque - (-n)` **aumenta** o estoque e reduz o total do pedido (`models.py:146,164`). E-mail não tem formato nem unicidade (`database.py:30`).
- **Impacto:** Erros de cliente viram `500`; manipulação de estoque e de valores de pedido por entrada negativa; usuários duplicados.
- **Recomendação:** Validação na fronteira com função/schema compartilhado: tipos numéricos, inteiros positivos para quantidade, corpo JSON obrigatório, `400` consistente.

### [MEDIUM] Validação duplicada e inconsistente entre criar e atualizar produto
- **Local:** `controllers.py:24-54` vs `controllers.py:64-90`
- **Evidência:** `criar_produto` valida tamanho do nome (`controllers.py:47-50`) e categoria (`controllers.py:52-54`); `atualizar_produto` repete as checagens de presença/negativos mas omite tamanho e categoria.
- **Impacto:** Via `PUT` é possível gravar nome vazio/longo e categoria inválida que o `POST` rejeita.
- **Recomendação:** Um único validador de produto usado por create e update.

### [MEDIUM] Query N+1 na listagem de pedidos
- **Local:** `models.py:177-200`, `models.py:209-232`, `models.py:154-156`
- **Evidência:** para cada pedido, um `SELECT` em `itens_pedido` (`models.py:188,220`) e, para cada item, um `SELECT nome FROM produtos` (`models.py:192,224`); em `criar_pedido` o preço de cada produto é relido (`models.py:155`) após já ter sido lido em `models.py:140`.
- **Impacto:** 1 + P + I consultas por listagem; degrada linearmente com volume.
- **Recomendação:** Uma query de pedidos + uma query de itens com `JOIN produtos` filtrada por `pedido_id IN (...)`, agrupando em memória; reaproveitar os produtos já lidos na criação.

### [MEDIUM] Tratamento de erro opaco que expõe exceções internas
- **Local:** `controllers.py:10-12` (padrão repetido em todos os handlers: `21-22`, `60-62`, `95-96`, `108-109`, `125-126`, `133-134`, `143-144`, `164-165`, `185-186`, `218-220`, `226-227`, `234-235`, `254-255`, `261-262`, `291-292`), `app.py:77-78`
- **Evidência:** `except Exception as e: return jsonify({"erro": str(e)}), 500`.
- **Impacto:** Mensagens internas (SQL, nomes de tabelas, tipos) são devolvidas ao cliente — o que ainda facilita explorar a injeção SQL; erros de validação viram 500.
- **Recomendação:** Error handlers centralizados (`@app.errorhandler`), exceções de domínio mapeadas para 400/404/409 e 500 genérico com log no servidor.

### [MEDIUM] Duplicação de serialização e consultas
- **Local:** `models.py:12-21`, `models.py:31-40`, `models.py:304-313`; `models.py:78-86` / `models.py:95-102`; `models.py:171-201` / `models.py:203-233`
- **Evidência:** o mesmo dicionário de produto escrito três vezes; o mesmo de usuário duas vezes; `get_pedidos_usuario` e `get_todos_pedidos` são cópias diferindo só no `WHERE`.
- **Impacto:** Mudanças de contrato precisam ser replicadas manualmente (foi assim que `senha` vazou em dois lugares).
- **Recomendação:** Funções únicas `_produto_to_dict`, `_usuario_to_dict` (sem senha) e uma consulta de pedidos parametrizada por filtro.

### [LOW] Magic numbers/strings
- **Local:** `controllers.py:52`, `controllers.py:242`, `models.py:247-253`, `models.py:257-262`, `app.py:36`, `controllers.py:285`
- **Evidência:** lista de categorias e de status inline; faixas de desconto `10000/5000/1000` e taxas `0.1/0.05/0.02`; versão `"1.0.0"` repetida; `"ambiente": "producao"` fixo.
- **Recomendação:** Constantes nomeadas no domínio (categorias, status, faixas de desconto, versão).

### [LOW] Logging via `print` com dados pessoais
- **Local:** `controllers.py:8`, `11`, `57`, `61`, `106`, `161`, `179`, `182`, `208-210`, `219`, `248`, `250`; `app.py:56`, `app.py:83-86`
- **Evidência:** `print("Login falhou: " + email)`, `print("Usuário criado: " + email)`.
- **Recomendação:** Módulo `logging` com níveis; não registrar e-mails/credenciais.

### [LOW] Imports não usados e nomes que sombreiam builtins
- **Local:** `models.py:2` (`import sqlite3` não usado), `database.py:2` (`import os` não usado); parâmetro/variável `id` em `controllers.py:14,56,64,98,136,160` e `models.py:24,54,65,89`.
- **Recomendação:** Remover imports; preferir `produto_id`/`usuario_id` internamente (mantendo os nomes das rotas).

## APIs deprecated
Nenhuma identificada após checagem do uso de Flask 3.1 (`add_url_rule`, `route`, `request.get_json`, `jsonify` — todos APIs atuais) e de `sqlite3` (não há uso de adaptadores/conversores de `datetime` padrão, deprecados no Python 3.12; nem `datetime.utcnow()`). Não foi rodado scanner de vulnerabilidades de dependências (`pip-audit`); nenhuma CVE é alegada.

## Gate da Fase 2
A auditoria não alterou o código-alvo. Aprovar a Fase 3? (sim/não)
