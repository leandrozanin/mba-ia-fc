# Análise de projeto

## Inventário seguro

- Leia `pyproject.toml`, `requirements*.txt`, `Pipfile`, `package.json` e lockfiles para identificar dependências e versões declaradas.
- Use arquivos executáveis/importados como evidência da stack; um arquivo de dependência isolado não prova uso de um framework.
- Ignore `.git`, `.venv`, `venv`, `node_modules`, `vendor`, `dist`, `build`, caches, arquivos minificados e dados gerados ao contar fontes.
- Identifique entradas em `app.py`, `main.py`, `wsgi.py`, `src/index.*`, `src/app.*`, comandos de scripts e configuração de servidor.
- Localize rotas/handlers, acesso a dados, modelos, serviços, middlewares, autenticação, serialização e tratamento de erros. Em aplicações pequenas, nomeie as responsabilidades encontradas sem impor camadas inexistentes.

## Heurísticas por stack

| Evidência | Linguagem/framework provável | Confirmação |
|---|---|---|
| `.py`, `requirements.txt`, imports `flask` | Python / Flask | app factory, `Flask(...)`, Blueprints e decorators de rota |
| `.py`, imports `django` | Python / Django | `manage.py`, settings, urls e views |
| `.js`/`.cjs`/`.mjs`, `package.json`, `express` | JavaScript / Express | `express()`, `app.use`, `app.get/post` ou Router |
| `.ts`, package scripts, `@nestjs/*` | TypeScript / NestJS | módulos, controllers e providers |
| `.java`, `pom.xml` ou Gradle | Java / framework indicado | annotations e dependências no manifesto |
| `.go`, `go.mod` | Go / framework indicado | imports e registro de handlers |

Detecte banco por driver, ORM, URL de conexão, schema ou migrations: SQLite (`sqlite3`, `better-sqlite3`), PostgreSQL (`psycopg`, `pg`), MySQL, SQLAlchemy, Prisma etc. Separe o banco declarado daquele realmente configurado. Não imprima valores de secrets encontrados; informe somente o caminho e o nome da variável/chave.

## Mapeamento arquitetural

1. Desenhe o fluxo de uma requisição: entrada/rota → validação → regra de negócio → persistência/integração → resposta.
2. Aponte os arquivos responsáveis e dependências entre eles; use um diagrama textual pequeno se ajudar.
3. Classifique com evidência: monólito concentrado, MVC parcial, camadas com dependências invertidas ou outro arranjo.
4. Conte arquivos de código realmente inspecionados e linhas aproximadas apenas quando calculadas. Registre comandos e limitações da análise.
5. Liste endpoints por método e rota a partir do registro real de rotas, não de documentação possivelmente desatualizada.
