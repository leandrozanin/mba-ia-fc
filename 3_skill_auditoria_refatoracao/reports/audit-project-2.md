# Relatório de Auditoria — ecommerce-api-legacy

## Análise do projeto
- **Linguagem/framework:** JavaScript (CommonJS) em Node.js v24.22.1 / Express 4.22.1 (instalado; declarado `^4.18.2` em `package.json`). Evidência: `express()`, `app.use(express.json())` e `app.post/get/delete` em `src/app.js` e `src/AppManager.js`.
- **Banco e dependências relevantes:** SQLite via `sqlite3` 5.1.7 (declarado `^5.1.6`), banco **em memória** (`new sqlite3.Database(':memory:')`, `src/AppManager.js:7`), schema e seeds criados no boot (`src/AppManager.js:10-23`). Tabelas: `users`, `courses`, `enrollments`, `payments`, `audit_logs` — sem chaves estrangeiras.
- **Domínio:** LMS com checkout — compra de curso (criação de usuário, pagamento simulado, matrícula, log de auditoria), relatório financeiro por curso e exclusão de usuário.
- **Arquitetura atual:** monólito concentrado. `src/app.js` (composition root) → `AppManager` (conexão, schema, seeds, rotas, regras de negócio, pagamento, auditoria e relatório) → `sqlite3`. `src/utils.js` mistura configuração com segredos, cache global e "hash" de senha. Não há camadas de model, controller ou router.
- **Endpoints registrados (`src/AppManager.js`):**
  - `POST /api/checkout` (linha 28)
  - `GET /api/admin/financial-report` (linha 80)
  - `DELETE /api/users/:id` (linha 131)
- **Arquivos-fonte analisados / excluídos:** 3 arquivos-fonte analisados — `src/app.js` (14 linhas), `src/AppManager.js` (141), `src/utils.js` (25). Também lidos: `package.json`, `README.md`, `api.http`. Excluídos: `node_modules/`, `package-lock.json` (gerado), `.claude/` (ferramental do agente).
- **Comandos de teste e boot disponíveis:** boot com `npm start` (`node src/app.js`, porta 3000). **Não há testes** nem script `test` em `package.json`. Requisições de exemplo em `api.http`.

## Resumo
| Severidade | Quantidade |
|---|---:|
| CRITICAL | 3 |
| HIGH | 5 |
| MEDIUM | 4 |
| LOW | 3 |
| **Total** | **15** |

## Achados

### [CRITICAL] Segredos embutidos no código
- **Local:** `src/utils.js:2-5`
- **Evidência:** o objeto `config` contém literais para `dbUser`, `dbPass`, `paymentGatewayKey` (prefixo de chave *live*) e `smtpUser`. Valores omitidos neste relatório.
- **Descrição:** credenciais de banco e chave do gateway de pagamento ficam versionadas no código-fonte.
- **Impacto:** qualquer pessoa com acesso ao repositório obtém as credenciais; rotação exige deploy; o mesmo valor serve a todos os ambientes.
- **Recomendação:** carregar via variáveis de ambiente/secret store com validação na inicialização, remover os literais e rotacionar as chaves caso sejam reais.

### [CRITICAL] Número de cartão e chave do gateway gravados em log
- **Local:** `src/AppManager.js:45`
- **Evidência:** `` console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`) ``
- **Descrição:** a cada checkout o número completo do cartão (PAN) e a chave do gateway são escritos no stdout.
- **Impacto:** vazamento de dados de cartão e do segredo para qualquer destino de log (agregadores, arquivos, terceiros); violação direta de requisitos PCI-DSS.
- **Recomendação:** remover o log; se necessário, registrar apenas identificador da transação ou os 4 últimos dígitos, nunca a chave.

### [CRITICAL] God class `AppManager`
- **Local:** `src/AppManager.js:7` (conexão), `10-23` (schema e seeds), `28-78` (checkout), `80-129` (relatório), `131-137` (exclusão)
- **Evidência:** uma única classe abre a conexão, cria tabelas, insere seeds, registra todas as rotas HTTP, decide pagamento, persiste em 4 tabelas, grava auditoria, alimenta cache e monta o relatório financeiro.
- **Descrição:** roteamento, regras de três casos de uso, persistência e integração de pagamento estão no mesmo módulo, sem fronteiras.
- **Impacto:** impossível testar unidades isoladamente (não há testes); qualquer mudança afeta todos os fluxos; dificulta trocar banco ou gateway.
- **Recomendação:** separar em routers Express, controllers por caso de uso, models/repositories por tabela, serviço de pagamento e módulo de inicialização de banco, com dependências injetadas (ver `mvc-guidelines.md`).

### [HIGH] Armazenamento de senha com "hash" inseguro e senha padrão
- **Local:** `src/utils.js:17-23`; `src/AppManager.js:68`; `src/AppManager.js:18`
- **Evidência:** `badCrypto` concatena 10.000 vezes `Buffer.from(pwd).toString('base64').substring(0, 2)` e devolve os 10 primeiros caracteres; o checkout usa `badCrypto(p || "123456")`; o seed grava a senha em texto puro.
- **Descrição:** o resultado é uma codificação reversível que depende apenas dos dois primeiros caracteres base64 (≈ primeiro byte e meio da senha), sem sal; quando `pwd` não é enviado, é atribuída uma senha fixa.
- **Impacto:** senhas que começam igual produzem o mesmo "hash"; um vazamento da tabela revela o prefixo das senhas; contas criadas sem senha compartilham uma senha conhecida; o loop de 10.000 iterações gasta CPU sem ganho de segurança.
- **Recomendação:** usar `crypto.scrypt`/bcrypt/argon2 com sal; exigir senha no cadastro (ou definir fluxo sem senha explícito) e não gravar senha em texto puro no seed.

### [HIGH] Regra de negócio dentro dos handlers de rota
- **Local:** `src/AppManager.js:28-78` e `src/AppManager.js:80-129`
- **Evidência:** o handler de checkout decide aprovação de pagamento (`cc.startsWith("4") ? "PAID" : "DENIED"`, linha 46), cria usuário, matrícula, pagamento e auditoria em callbacks aninhados; o handler do relatório calcula receita e agrega alunos.
- **Descrição:** o workflow completo vive no callback HTTP.
- **Impacto:** a regra não pode ser reutilizada nem testada sem subir o servidor; o aninhamento de 5 níveis de callback dificulta tratar erros corretamente (ver achados de transação e erro).
- **Recomendação:** rotas apenas adaptam HTTP; um controller/serviço de checkout coordena repositórios e um `PaymentGateway`; um serviço de relatório faz a agregação.

### [HIGH] Checkout sem controle transacional
- **Local:** `src/AppManager.js:66-72`, `48`, `50-61`
- **Evidência:** o usuário novo é inserido (linha 69) **antes** da decisão de pagamento; se o pagamento é recusado, a linha 48 responde 400 e o usuário permanece. Matrícula (50) e pagamento (54) são inserts independentes; se o segundo falhar, a matrícula fica sem pagamento. O erro do insert de `audit_logs` (57) é ignorado e a resposta é 200.
- **Descrição:** escritas em várias tabelas sem `BEGIN/COMMIT/ROLLBACK`.
- **Impacto:** usuários criados em checkouts recusados, matrículas sem pagamento e checkouts sem auditoria — dados inconsistentes que distorcem o relatório financeiro.
- **Recomendação:** validar pagamento antes de qualquer escrita e executar usuário/matrícula/pagamento/auditoria numa transação única com rollback em falha; cobrir com testes de falha intermediária.

### [HIGH] Endpoints administrativos e destrutivos sem autenticação/autorização
- **Local:** `src/AppManager.js:80` e `src/AppManager.js:131`
- **Evidência:** `app.get('/api/admin/financial-report', ...)` e `app.delete('/api/users/:id', ...)` são registrados sem nenhum middleware; `src/app.js:6` registra apenas `express.json()`.
- **Descrição:** qualquer cliente pode ler o relatório financeiro (nomes de alunos e valores pagos) e apagar qualquer usuário por id.
- **Impacto:** exposição de dados pessoais/financeiros e exclusão arbitrária de contas.
- **Recomendação:** adicionar middleware de autenticação e autorização por papel (admin) nessas rotas. A escolha do mecanismo depende de requisito ainda inexistente no projeto e deve ser acordada antes da Fase 3.

### [HIGH] Exclusão de usuário sem integridade referencial e com erro ignorado
- **Local:** `src/AppManager.js:131-137`; schema em `src/AppManager.js:12-15`
- **Evidência:** `DELETE FROM users WHERE id = ?` com callback que ignora `err` e sempre responde 200 com a mensagem "Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."; as tabelas não declaram `FOREIGN KEY`.
- **Descrição:** matrículas e pagamentos do usuário ficam órfãos; falhas de banco e ids inexistentes também retornam sucesso.
- **Impacto:** o relatório financeiro passa a listar alunos `'Unknown'` (linha 113) mantendo a receita; o cliente não distingue sucesso, falha ou usuário inexistente.
- **Recomendação:** definir a política (cascata, soft delete ou bloqueio quando houver pagamentos), aplicá-la numa transação, retornar 404 para id inexistente e 500 em erro.

### [MEDIUM] Estado global mutável e acoplamento rígido
- **Local:** `src/utils.js:9-15`, `src/utils.js:25`; `src/AppManager.js:2`, `src/AppManager.js:7`
- **Evidência:** `globalCache` é um objeto de módulo que recebe uma chave por usuário a cada checkout (`logAndCache`, linha 59 de `AppManager.js`) e nunca é lido nem limpo; `totalRevenue` é `let` global exportado; `AppManager` instancia o driver SQLite concretamente no construtor.
- **Descrição:** estado compartilhado de processo e dependências concretas criadas internamente.
- **Impacto:** crescimento de memória sem limite proporcional ao número de usuários; impossível injetar banco temporário ou fake em testes.
- **Recomendação:** remover o cache sem leitores (ou substituí-lo por um componente com TTL/limite e injetado) e receber a conexão de banco por injeção a partir do composition root.

### [MEDIUM] Query N+1 no relatório financeiro
- **Local:** `src/AppManager.js:83`, `92`, `104`, `106`
- **Evidência:** 1 consulta de cursos, depois 1 consulta de matrículas por curso e, para cada matrícula, 1 consulta de usuário e 1 de pagamento.
- **Descrição:** o total de queries é `1 + C + 2·E` (C = cursos, E = matrículas).
- **Impacto:** latência e carga crescem linearmente com o número de matrículas; a ordem de `report`/`students` depende da ordem de conclusão dos callbacks.
- **Recomendação:** uma única consulta com `LEFT JOIN` de `courses`/`enrollments`/`users`/`payments` e agregação em memória (ou `SUM ... GROUP BY`), preservando o formato atual da resposta.

### [MEDIUM] Tratamento de erro opaco e que derruba o processo
- **Local:** `src/AppManager.js:38`, `57`, `92-93`, `104-106`, `133`
- **Evidência:** linha 38 converte erro de banco em `404 "Curso não encontrado"`; nas linhas 92, 104 e 106 `err` é ignorado — se a consulta da linha 92 falhar, `enrollments` é `undefined` e `enrollments.length` (linha 93) lança `TypeError` dentro do callback do driver, sem captura, encerrando o processo; erros das linhas 57 e 133 são ignorados com resposta de sucesso.
- **Descrição:** não há middleware de erro; respostas misturam texto puro e JSON.
- **Impacto:** falhas de banco aparecem como sucesso ou 404, e uma falha pontual pode derrubar a API inteira.
- **Recomendação:** promisificar o acesso a dados, propagar erros a um middleware central com log seguro e status consistentes (preservando os corpos atuais onde o contrato exigir).

### [MEDIUM] Falta de validação de entrada
- **Local:** `src/AppManager.js:29-35`, `46`, `132`
- **Evidência:** a linha 35 só verifica presença de `usr`, `eml`, `c_id`, `card`; não valida tipo nem formato. `cc.startsWith("4")` (linha 46) lança `TypeError` se `card` vier como número JSON (`"card": 4111222233334444`), dentro de callback assíncrono, encerrando o processo. `eml` não tem validação de formato e `req.params.id` não é validado.
- **Descrição:** entrada usada diretamente nas regras e na persistência.
- **Impacto:** um único request malformado derruba o servidor; dados inválidos são gravados.
- **Recomendação:** validar na fronteira (strings não vazias, e-mail, `c_id` inteiro positivo, cartão só com dígitos e tamanho válido, `id` inteiro) e responder 400 de forma consistente.

### [LOW] Código morto e símbolos não usados
- **Local:** `src/AppManager.js:2` (`totalRevenue`), `src/utils.js:2-3`, `5` (`dbUser`, `dbPass`, `smtpUser`), `src/utils.js:10`, `25` (`totalRevenue`, `globalCache` exportados)
- **Evidência:** `totalRevenue` é importado e nunca usado; as chaves de config citadas não são referenciadas em nenhum arquivo; `globalCache` é exportado e não é lido.
- **Descrição:** símbolos sem efeito.
- **Impacto:** ruído e falsa impressão de que existem integrações de banco remoto/SMTP.
- **Recomendação:** remover após a extração de configuração.

### [LOW] Nomenclatura obscura e logging improvisado
- **Local:** `src/AppManager.js:26`, `29-33`; `src/utils.js:13`; `src/app.js:13`
- **Evidência:** variáveis `u`, `e`, `p`, `cid`, `cc`; alias `self = this` misturado com `this` em arrow functions; `console.log` como único mecanismo de log; nome `badCrypto`.
- **Descrição:** nomes não revelam intenção e não há logger com níveis.
- **Impacto:** leitura e manutenção mais difíceis. Os campos públicos do payload (`usr`, `eml`, `pwd`, `c_id`, `card`) fazem parte do contrato e não devem ser renomeados sem plano de compatibilidade.
- **Recomendação:** nomes descritivos internamente, logger com níveis e sem dados sensíveis.

### [LOW] Magic numbers/strings
- **Local:** `src/AppManager.js:21`, `46`, `48`, `68`, `108`; `src/utils.js:6`, `19`
- **Evidência:** status `'PAID'`/`'DENIED'` repetidos; regra de aprovação pelo prefixo `"4"`; senha padrão `"123456"`; porta `3000` fixa; `10000` iterações.
- **Descrição:** valores de domínio sem nome nem ponto único de definição.
- **Impacto:** risco de divergência ao alterar um dos usos; a regra de aprovação simulada não fica explícita como simulação.
- **Recomendação:** constantes/enum de status de pagamento, porta via variável de ambiente com default e encapsular a simulação de pagamento num gateway nomeado.

## APIs deprecated
Nenhuma identificada após checagem das APIs usadas contra as versões instaladas: Express 4.22.1 (`express()`, `express.json()`, `app.get/post/delete`, `res.status().send()`, `res.json()`, `req.params`/`req.body` — nenhuma das assinaturas deprecated do Express 4, como `res.send(status)` ou `req.param()`, é usada) e sqlite3 5.1.7 (`Database`, `serialize`, `run`, `get`, `all`, `verbose`). Observação: não foi executado `npm audit`; nenhuma CVE de dependência é alegada neste relatório.

## Gate da Fase 2
A auditoria não alterou o código-alvo. Aprovar a Fase 3? (sim/não)

**Resposta:** aprovada, com a decisão de autenticar as rotas administrativas e de exclusão com um token de admin vindo de variável de ambiente.

## Fase 3 — Resultado da refatoração

### Baseline (código original, `npm start`)
| Requisição | Status / corpo |
|---|---|
| `GET /api/admin/financial-report` (sem auth) | 200, JSON; ordem dos cursos variou entre execuções |
| `POST /api/checkout` sucesso (`api.http`) | 200 `{"msg":"Sucesso","enrollment_id":2}` |
| `POST /api/checkout` cartão `5…` | 400 `Pagamento recusado` (usuário era criado mesmo assim) |
| `POST /api/checkout` sem `c_id`/`card` | 400 `Bad Request` |
| `POST /api/checkout` `c_id` 99 | 404 `Curso não encontrado` |
| `DELETE /api/users/1` (sem auth) | 200; relatório passa a mostrar `Unknown` com receita mantida |
| `POST /api/checkout` com `card` numérico | **processo encerrado** (`TypeError` em `cc.startsWith`, cliente recebe `ECONNRESET`) |

Não havia testes.

### Estrutura antes → depois
- **Antes:** `src/app.js`, `src/AppManager.js` (god class), `src/utils.js` (config com segredos, cache global, hash fraco).
- **Depois:** `src/app.js` (composition root `createApp` + boot só quando executado diretamente), `src/config/`, `src/db/` (wrapper com Promises e transações enfileiradas, schema com FKs `ON DELETE CASCADE`, seeds), `src/models/` (users, courses, enrollments, payments, audit_logs), `src/services/` (checkout, relatório, gateway de pagamento simulado, hash scrypt), `src/controllers/` (+ validação), `src/routes/`, `src/middlewares/` (auth de admin, error handler), `src/errors.js`, `test/api.test.js`.

### Achados tratados
| Achado | Tratamento |
|---|---|
| Segredos embutidos | Literais removidos; `ADMIN_TOKEN` (obrigatório), `PORT`, `DB_FILE`, `PAYMENT_GATEWAY_KEY` vêm do ambiente. **Rotacione as chaves antigas caso fossem reais** — continuam no histórico do git. |
| Cartão/chave em log | Log removido; o servidor só registra o boot e erros 500 (método, rota e mensagem). |
| God class | `AppManager` removida e dividida nas camadas acima. |
| Hash de senha | `crypto.scrypt` com sal aleatório; senha obrigatória para criar usuário novo; seed também com hash. |
| Regra de negócio na rota | Rotas apenas registram handlers; controllers validam e delegam a serviços. |
| Falta de transação | Pagamento decidido antes de qualquer escrita; usuário/matrícula/pagamento/auditoria em uma transação com rollback. |
| Rotas admin sem auth | Middleware `Authorization: Bearer <ADMIN_TOKEN>` com comparação em tempo constante → 401 `Unauthorized`. |
| Exclusão sem integridade | Cascata de matrículas e pagamentos via FK, em transação; 404 para id inexistente, 400 para id inválido. |
| Estado global | `globalCache`/`totalRevenue` removidos; dependências injetadas a partir do composition root. |
| N+1 | Relatório usa uma única consulta com `LEFT JOIN`, ordenada por curso e matrícula. |
| Erros opacos | Error handler central; erros de banco viram 500 em vez de 404/sucesso falso; nada derruba o processo. |
| Validação | `usr`/`eml` (formato), `c_id` inteiro positivo, `card` string de 12–19 dígitos, `pwd` string não vazia quando presente, `:id` inteiro; JSON malformado → 400. |
| Código morto, nomes, magic values | Removidos/renomeados; `PAYMENT_STATUS`, prefixo aprovado e porta padrão nomeados. Campos públicos do payload mantidos. |

### Validação executada
- `npm test` → **12 testes, 12 aprovados, 0 falhas** (checkout, recusa sem efeitos colaterais, 404, entradas inválidas, rollback em falha intermediária, auth 401, formato do relatório, exclusão em cascata, 404/400 na exclusão, checkouts concorrentes). Cada teste usa um SQLite em memória próprio.
- `npm start` sem `ADMIN_TOKEN` → encerra com `[FATAL] Variável de ambiente ADMIN_TOKEN é obrigatória`.
- `ADMIN_TOKEN=… npm start` + as mesmas requisições do baseline: sucesso 200 com o mesmo JSON; recusa 400 `Pagamento recusado`; payload incompleto 400 `Bad Request`; relatório 200 com o mesmo formato; rotas admin sem token 401; `card` numérico 400 com o servidor ainda de pé; o log não contém o número do cartão nem a chave.

### Mudanças de contrato intencionais
- `GET /api/admin/financial-report` e `DELETE /api/users/:id` exigem `Authorization: Bearer <ADMIN_TOKEN>`.
- `DELETE /api/users/:id`: corpo de sucesso agora é `Usuário deletado, junto com suas matrículas e pagamentos.`; 404 `Usuário não encontrado`; 400 para id inválido; o relatório deixa de contar a receita do usuário excluído.
- `POST /api/checkout`: entradas antes aceitas agora retornam 400 (cartão fora de 12–19 dígitos, e-mail sem formato, usuário novo sem `pwd`). Como a validação vem antes da busca do curso, uma requisição com `c_id` inexistente **e** cartão inválido (ex.: `"4111"`) retorna 400, não 404. Erros de banco retornam 500 `Erro DB` em vez de 404.
- O relatório tem ordem determinística (curso por id, depois matrícula).

### Limitações
- O gateway de pagamento continua simulado (aprova cartões iniciados por `4`); `PAYMENT_GATEWAY_KEY` é só repassada.
- As transações são serializadas numa conexão SQLite compartilhada. Leituras de outras requisições ainda podem rodar entre os comandos de uma transação aberta e ver dados não commitados.
- Não há login, então `verifyPassword` só é exercida pelos testes.
- `npm audit` não foi executado.
