# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
export SECRET_KEY="<valor aleatório longo>"      # obrigatório
export ADMIN_EMAIL="admin@loja.com"              # opcional: cria o admin inicial
export ADMIN_PASSWORD="<senha forte>"            # obrigatório junto com ADMIN_EMAIL
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000`. O banco SQLite é criado automaticamente no primeiro boot, já com produtos de exemplo. Bancos criados por versões anteriores são aproveitados: senhas em texto puro são convertidas para hash no boot.

### Variáveis de ambiente

| Variável | Padrão | Uso |
|---|---|---|
| `SECRET_KEY` | — (obrigatória) | Assina os tokens de autenticação |
| `DATABASE_PATH` | `loja.db` | Caminho do arquivo SQLite |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | Endereço do servidor |
| `FLASK_DEBUG` | `false` | Modo debug (nunca em produção) |
| `CORS_ORIGINS` | vazio (CORS desligado) | Origens permitidas, separadas por vírgula |
| `TOKEN_MAX_AGE` | `28800` | Validade do token em segundos |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | — | Cria o usuário admin inicial se ainda não existir |
| `ENABLE_ADMIN_RESET` | `false` | Habilita `POST /admin/reset-db` (somente admin) |

## Autenticação

`POST /login` devolve um `token`; envie-o como `Authorization: Bearer <token>`.

| Acesso | Rotas |
|---|---|
| Público | `GET /`, `GET /health`, `GET /produtos`, `GET /produtos/busca`, `GET /produtos/<id>`, `POST /usuarios`, `POST /login` |
| Usuário autenticado | `POST /pedidos` (para si), `GET /usuarios/<id>` e `GET /pedidos/usuario/<id>` (próprios) |
| Admin | escrita de produtos, `GET /usuarios`, `GET /pedidos`, `PUT /pedidos/<id>/status`, `GET /relatorios/vendas`, `POST /admin/reset-db` |

## Estrutura

```
app.py                 entry point (create_app + app.run)
loja/__init__.py       factory create_app: config, banco, blueprints, error handlers
loja/config.py         configuração vinda do ambiente
loja/db.py             conexão por requisição, transações, schema/seed/migração
loja/routes/           blueprints: adaptação HTTP
loja/controllers/      casos de uso (sem dependência de request)
loja/models/           acesso a dados com SQL parametrizado
loja/validators.py     validação de entrada
loja/auth.py           token e decorators de autenticação
loja/permissoes.py     regras de autorização
loja/notificacoes.py   notificador (log) injetável
tests/                 testes (unittest)
```

## Testes

```bash
python -m unittest discover -s tests -t . -v
```
