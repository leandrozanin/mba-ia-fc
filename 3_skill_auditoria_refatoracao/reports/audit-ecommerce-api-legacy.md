# Relatório de Auditoria — ecommerce-api-legacy

## Análise do projeto
- **Linguagem/framework:** JavaScript (Node.js, CommonJS) / Express 4. Evidência: `src/app.js:1,5-6` (`require('express')`, `express()`, `express.json()`), rotas registradas com `app.post/get/delete` em `src/AppManager.js:28,80,131`. `package.json` declara `express ^4.18.2`; `package-lock.json` resolve `express 4.22.1`.
- **Banco e dependências relevantes:** SQLite via `sqlite3` (lock: `5.1.7`), banco **em memória** (`new sqlite3.Database(':memory:')`, `src/AppManager.js:7`). Schema de 5 tabelas (`users`, `courses`, `enrollments`, `payments`, `audit_logs`) e seed criados no boot (`src/AppManager.js:10-23`), sem migrations, chaves estrangeiras ou índices únicos. `config` declara credenciais de banco/SMTP/gateway (`src/utils.js:1-7`) que não são usadas para conexão real — banco declarado ≠ banco configurado.
- **Domínio:** LMS (plataforma de cursos) com checkout: compra de curso com criação implícita de usuário, matrícula, pagamento simulado e log de auditoria; relatório financeiro por curso; remoção de usuário.
- **Arquitetura atual:** monólito concentrado em uma classe. Fluxo de requisição:
  ```
  src/app.js (bootstrap: express + new AppManager + listen)
     └─> src/AppManager.js (conexão DB + DDL + seed + rotas + validação +
                            regra de pagamento + criação de usuário + matrícula +
                            auditoria + relatório)
            └─> src/utils.js (config com segredos fixos, cache global, "hash" de senha)
  ```
  Não há controllers, models, services, middleware de erro, autenticação nem testes.
- **Arquivos-fonte analisados / excluídos:** 3 arquivos JS analisados integralmente — `src/app.js` (14 linhas), `src/AppManager.js` (141), `src/utils.js` (25) — total ≈ 180 linhas; também `package.json`, `README.md` e `api.http`. `package-lock.json` foi consultado só para versões resolvidas e não entra na contagem. Não há `node_modules` no diretório.
- **Comandos de teste e boot disponíveis:** boot `npm install && npm start` (`node src/app.js`, porta 3000 fixa em `src/utils.js:6`). **Não há script de teste nem testes.** Limitação: nesta fase a aplicação não foi executada; análise estática.

### Endpoints (a partir do registro real em `src/AppManager.js`)
| Método | Rota | Linha | Corpo/parâmetros |
|---|---|---|---|
| POST | `/api/checkout` | 28 | JSON `usr`, `eml`, `pwd` (opcional), `c_id`, `card` |
| GET | `/api/admin/financial-report` | 80 | — |
| DELETE | `/api/users/:id` | 131 | `id` na rota |

## Resumo
| Severidade | Quantidade |
|---|---:|
| CRITICAL | 2 |
| HIGH | 6 |
| MEDIUM | 4 |
| LOW | 3 |
| **Total** | **15** |

## Achados

### [CRITICAL] Segredos embutidos no código e chave do gateway impressa em log
- **Local:** `src/utils.js:2-5`, `src/AppManager.js:45`
- **Evidência:** objeto `config` com `dbUser`, `dbPass`, `paymentGatewayKey` (prefixo de chave *live*) e `smtpUser` como literais versionados (`src/utils.js:2-5`; valores omitidos). Em cada checkout: `` console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`) `` (`src/AppManager.js:45`).
- **Descrição:** Credenciais ficam no repositório e a chave de pagamento é escrita no stdout a cada requisição de checkout.
- **Impacto:** Qualquer pessoa com acesso ao código ou aos logs obtém a chave do gateway e a senha de banco; logs costumam ser enviados a sistemas de terceiros.
- **Recomendação:** Ler configuração de variáveis de ambiente (`process.env`) com validação no boot; remover a chave dos logs; tratar os valores atuais como comprometidos e rotacioná-los se forem reais.

### [CRITICAL] God class `AppManager`
- **Local:** `src/AppManager.js:4-139`
- **Evidência:** a mesma classe abre a conexão (`:7`), cria schema e seed (`:10-23`), registra todas as rotas (`:25-138`), valida entrada (`:35`), decide pagamento (`:46`), cria usuário com "hash" (`:66-72`), grava matrícula/pagamento/auditoria (`:50-61`), escreve cache (`:59`) e monta o relatório financeiro (`:80-129`).
- **Descrição:** Roteamento, regras de três domínios (usuários, matrículas/pagamentos, relatórios), persistência e integrações estão no mesmo método `setupRoutes`, com callbacks aninhados em até 6 níveis (`:37-63`, `:83-128`).
- **Impacto:** Nenhuma regra pode ser testada isoladamente; qualquer mudança no checkout ou no relatório exige mexer no mesmo bloco de callbacks, com alto risco de regressão (respostas duplicadas ou nunca enviadas).
- **Recomendação:** Separar em `config`, `db` (conexão/schema/seed), models/repositórios por entidade, services (`checkoutService`, `reportService`, `userService`), controllers finos e `routes`, com `async/await` sobre a API de callbacks.

### [HIGH] Número completo do cartão registrado em log
- **Local:** `src/AppManager.js:45`
- **Evidência:** `${cc}` (valor bruto de `req.body.card`) interpolado no `console.log`.
- **Descrição:** O PAN completo é persistido em stdout/logs a cada checkout.
- **Impacto:** Exposição de dados de cartão a quem lê logs; incompatível com práticas PCI-DSS.
- **Recomendação:** Nunca logar o cartão; quando necessário, registrar apenas os 4 últimos dígitos.

### [HIGH] Endpoints administrativos e destrutivos sem autenticação/autorização
- **Local:** `src/AppManager.js:80-129`, `src/AppManager.js:131-137`, `src/AppManager.js:40-75`
- **Evidência:** `GET /api/admin/financial-report` devolve receita e nomes de alunos com valores pagos; `DELETE /api/users/:id` remove qualquer usuário; nenhuma rota tem middleware de autenticação. No checkout, se o e-mail já existe, o usuário existente é usado sem conferir senha (`:73-75`) — `usr`/`pwd` são ignorados.
- **Impacto:** Qualquer cliente lê dados financeiros e pessoais, apaga contas e cria matrículas/pagamentos em nome de outra pessoa sabendo só o e-mail dela.
- **Recomendação:** Middleware de autenticação e checagem de papel para `/api/admin/*` e `DELETE /api/users/:id`, com credencial vinda de configuração; no checkout, exigir senha correta para usuário existente (ou autenticação prévia).

### [HIGH] "Hash" de senha inseguro e senha padrão
- **Local:** `src/utils.js:17-23`, `src/AppManager.js:68`, `src/AppManager.js:18`
- **Evidência:** `badCrypto` repete os 2 primeiros caracteres do Base64 da senha e corta em 10 — o resultado depende apenas do início da senha e é reversível; o laço de 10.000 iterações não adiciona custo criptográfico. Sem `pwd`, a senha vira `"123456"` (`:68`). O seed grava senha em texto puro (`:18`).
- **Impacto:** Senhas com o mesmo prefixo têm o mesmo "hash"; vazamento da tabela `users` equivale a vazamento das senhas; contas criadas sem senha recebem uma senha trivial conhecida.
- **Recomendação:** `crypto.scrypt`/`pbkdf2` (stdlib do Node) com salt aleatório e comparação em tempo constante; rejeitar checkout de usuário novo sem senha; seed com senha já hasheada.

### [HIGH] Checkout sem controle transacional
- **Local:** `src/AppManager.js:66-72`, `src/AppManager.js:46-48`, `src/AppManager.js:50-61`
- **Evidência:** o usuário novo é inserido (`:69`) **antes** da decisão de pagamento (`:46-48`), então um pagamento recusado deixa o usuário criado; matrícula (`:50`), pagamento (`:54`) e auditoria (`:57`) são três `INSERT`s independentes, sem `BEGIN/COMMIT/ROLLBACK`.
- **Impacto:** Falha no `INSERT` de pagamento deixa matrícula sem pagamento (aluno matriculado sem pagar); recusas acumulam usuários órfãos.
- **Recomendação:** Decidir pagamento antes de qualquer escrita e executar usuário + matrícula + pagamento + auditoria numa transação com rollback em erro.

### [HIGH] Regra de negócio no handler de rota
- **Local:** `src/AppManager.js:28-78`
- **Evidência:** aprovação de pagamento `cc.startsWith("4") ? "PAID" : "DENIED"` (`:46`), política de criação implícita de usuário e de senha padrão (`:66-72`) e escrita de auditoria/cache (`:57-59`) dentro do callback da rota.
- **Impacto:** A regra de pagamento simulado não pode ser substituída por um gateway real nem testada sem HTTP e banco.
- **Recomendação:** Mover para `checkoutService` com um `paymentGateway` injetável; a rota só traduz request/response.

### [HIGH] Estado global mutável e acoplamento rígido
- **Local:** `src/utils.js:9-15`, `src/utils.js:6`, `src/AppManager.js:7`, `src/app.js:8-12`
- **Evidência:** `globalCache` módulo-global cresce a cada checkout sem limite nem leitura (`logAndCache`, `:12-15`); porta e caminho do banco fixos (`:6`, `':memory:'`); `app.js` instancia `AppManager` e chama `listen` no import, sem exportar `app`.
- **Impacto:** Vazamento de memória proporcional ao número de usuários; impossível configurar banco/porta por ambiente ou subir a app em testes sem abrir porta real.
- **Recomendação:** Fábrica `createApp({ db, config })` exportada, `listen` apenas no entrypoint, configuração por ambiente; remover o cache sem leitor.

### [MEDIUM] Query N+1 no relatório financeiro
- **Local:** `src/AppManager.js:83-128`
- **Evidência:** 1 query de cursos, 1 por curso em `enrollments` (`:92`) e 2 por matrícula em `users` e `payments` (`:104`, `:106`).
- **Impacto:** 1 + C + 2E consultas por chamada; a ordem de `report` e de `students` depende da ordem de término dos callbacks (não determinística).
- **Recomendação:** Uma query com `LEFT JOIN enrollments/users/payments` e agregação em memória, preservando o formato `[{course, revenue, students:[{student, paid}]}]`.

### [MEDIUM] Tratamento de erro ausente ou enganoso, com risco de queda do processo
- **Local:** `src/AppManager.js:92-93`, `src/AppManager.js:104-106`, `src/AppManager.js:57`, `src/AppManager.js:133-135`, `src/AppManager.js:38`
- **Evidência:** `err` é ignorado em `:92` e em seguida `enrollments.length` é lido — em erro, `enrollments` é `undefined` e o `TypeError` dentro do callback derruba o processo. `err` ignorado também em `:104`, `:106`, `:57` (falha de auditoria responde sucesso) e `:133` (DELETE responde 200 mesmo com erro ou id inexistente). Em `:38`, erro de banco vira `404 Curso não encontrado`.
- **Impacto:** Indisponibilidade total por um erro de query; respostas de sucesso falsas; diagnóstico mascarado.
- **Recomendação:** `async/await` com promessas, middleware de erro do Express com 500 genérico e log seguro, 404 quando `changes === 0`.

### [MEDIUM] Exclusão de usuário deixa dados órfãos
- **Local:** `src/AppManager.js:131-137`, `src/AppManager.js:12-15`
- **Evidência:** apenas `DELETE FROM users`; schema sem `FOREIGN KEY`; a própria resposta diz "as matrículas e pagamentos ficaram sujos no banco".
- **Impacto:** `enrollments`/`payments` apontando para usuário inexistente; relatório passa a listar `student: 'Unknown'` (`:113`).
- **Recomendação:** Definir comportamento explícito (remover ou anonimizar matrículas/pagamentos dentro de transação, ou bloquear exclusão com histórico financeiro).

### [MEDIUM] Falta de validação de entrada no checkout
- **Local:** `src/AppManager.js:29-35`, `src/AppManager.js:46`, `src/AppManager.js:50`
- **Evidência:** só verifica presença (`:35`); `card` é usado com `.startsWith` — se não for string (ex.: número no JSON) lança `TypeError` dentro do callback e derruba o processo; sem validação de formato de e-mail, de `c_id` numérico nem de cartão; não há checagem de matrícula duplicada, então o mesmo aluno pode ser cobrado várias vezes pelo mesmo curso.
- **Impacto:** Queda do serviço com payload malformado; cobranças duplicadas; dados inconsistentes.
- **Recomendação:** Validador na fronteira (tipos, e-mail, `c_id` inteiro positivo, cartão string numérica) com `400`, e regra de unicidade `(user_id, course_id)`.

### [LOW] Código morto e imports não usados
- **Local:** `src/AppManager.js:2` (`totalRevenue` importado e nunca usado), `src/utils.js:10,25` (`totalRevenue` exportado por valor, sem efeito), `src/utils.js:2-3,5` (`dbUser`, `dbPass`, `smtpUser` sem uso), `src/utils.js:25` (`globalCache` exportado sem consumidor).
- **Recomendação:** Remover após a extração de configuração.

### [LOW] Nomenclatura obscura e estilos misturados
- **Local:** `src/AppManager.js:29-33`, `src/AppManager.js:26`
- **Evidência:** variáveis `u`, `e`, `p`, `cid`, `cc`; `const self = this` convivendo com arrow functions que usam `this`.
- **Recomendação:** Nomes de domínio internamente (`name`, `email`, `password`, `courseId`, `cardNumber`), mantendo os campos do contrato HTTP (`usr`, `eml`, `pwd`, `c_id`, `card`).

### [LOW] Magic strings/números e logging improvisado
- **Local:** `src/AppManager.js:46` (`"4"`, `"PAID"`, `"DENIED"`), `src/AppManager.js:68` (`"123456"`), `src/AppManager.js:108`, `src/utils.js:6` (`3000`), `src/utils.js:13`, `src/app.js:13`
- **Recomendação:** Constantes de status de pagamento; `console.log` substituído por logger com níveis e sem dados sensíveis.

## APIs deprecated
Nenhuma identificada após checagem do uso de Express 4.22 (`express.json()`, `app.get/post/delete`, `res.status().send/json` — sem as assinaturas removidas/deprecadas como `res.send(status)` ou `res.json(status, obj)`) e de `sqlite3` 5.1 (`Database`, `serialize`, `run`, `get`, `all`, `verbose()`). Não foi executado `npm audit` (sem `node_modules`); nenhuma CVE é alegada.

## Gate da Fase 2
A auditoria não alterou o código-alvo. Aprovar a Fase 3? (sim/não)
