# Relatorio de Auditoria — Projeto 1: code-smells-project

## Analise do projeto
- Linguagem/framework: Python 3.12 / Flask 3.1.1.
- Banco: SQLite via `sqlite3`; arquivo relativo `loja.db`.
- Dominio: API de e-commerce (produtos, usuarios, pedidos e relatorios).
- Arquitetura: rotas em `app.py`, handlers em `controllers.py`, SQL e varios dominios em `models.py`, conexao global em `database.py`.
- Arquivos-fonte analisados: 4 (`app.py`, `controllers.py`, `models.py`, `database.py`).
- Baseline: 10/10 rotas GET representativas responderam 200 pelo Flask test client. Nao ha suite de testes declarada.

## Resumo
| Severidade | Quantidade |
|---|---:|
| CRITICAL | 2 |
| HIGH | 1 |
| MEDIUM | 2 |
| LOW | 2 |
| **Total** | **7** |

## Achados

### [CRITICAL] Endpoint permite executar SQL arbitrario
- **Local:** `app.py:60-71`
- **Evidencia:** `/admin/query` aceita o campo `sql` do corpo e chama `cursor.execute(query)`; a rota nao possui autenticacao/autorizacao.
- **Descricao:** qualquer cliente que alcance a rota pode emitir consultas de leitura ou escrita no SQLite.
- **Impacto:** exposicao, alteracao ou exclusao direta dos dados da loja.
- **Recomendacao:** remover a rota de producao; para operacoes administrativas, exigir autorizacao e expor operacoes allowlisted, nunca SQL livre.

### [CRITICAL] Segredo fixo e debug habilitado
- **Local:** `app.py:7-8`
- **Evidencia:** `SECRET_KEY` e `DEBUG` recebem literais no entry point.
- **Descricao:** segredo versionado e modo debug sao configurados para qualquer ambiente.
- **Impacto:** risco de comprometimento de sessao e divulgacao de detalhes internos.
- **Recomendacao:** carregar segredo de ambiente validado e habilitar debug somente em desenvolvimento.

### [HIGH] Modulo de modelos concentra dominios e responsabilidades
- **Local:** `models.py:1-314`
- **Evidencia:** o arquivo implementa produtos, usuarios/login, pedidos, relatorios, SQL, formatacao de resposta e mutacoes de estoque.
- **Descricao:** regras e persistencia de varios dominios estao acopladas em um modulo.
- **Impacto:** mudancas ficam dificeis de isolar/testar; fluxos como pedido e estoque compartilham um modulo extenso.
- **Recomendacao:** separar repositorios/modelos por dominio e mover coordenacao para controllers/services coesos.

### [MEDIUM] Consultas N+1 ao carregar pedidos
- **Local:** `models.py:171-193` e `models.py:203-225`
- **Evidencia:** cada pedido busca itens e cada item busca o nome do produto com consultas dentro de loops.
- **Impacto:** latencia e carga crescem com pedidos e itens.
- **Recomendacao:** carregar itens e produtos com JOIN ou consultas em lote.

### [MEDIUM] Validacao de produto duplicada e inconsistente
- **Local:** `controllers.py:24-60` e `controllers.py:64-90`
- **Evidencia:** criacao e atualizacao repetem validacoes de campos/valores, mas a cobertura difere.
- **Impacto:** entradas equivalentes podem ser aceitas em um endpoint e rejeitadas em outro.
- **Recomendacao:** centralizar validacao em schema/helper e testar create/update com os mesmos limites.

### [LOW] Categorias e estados como literais de dominio
- **Local:** `controllers.py:52` e `controllers.py:242`
- **Evidencia:** valores permitidos estao em listas inline nos handlers.
- **Impacto:** alteracoes podem deixar rotas inconsistentes.
- **Recomendacao:** declarar constantes/enums de dominio compartilhados.

### [LOW] Logging operacional por print
- **Local:** `controllers.py:208`
- **Evidencia:** o fluxo de pedido emite mensagens diretamente ao stdout sem nivel ou politica de dados.
- **Impacto:** diagnostico e controle do que aparece nos logs ficam limitados.
- **Recomendacao:** usar logger configurado e nunca incluir dados sensiveis.

## APIs deprecated
Nenhuma API deprecated de Flask/SQLite foi confirmada no codigo de aplicacao analisado.

## Gate da Fase 2
A auditoria nao alterou a logica da aplicacao. Aprovar a Fase 3 para este projeto? Aguardar resposta explicita antes de alterar codigo, configuracao da aplicacao ou dados.
