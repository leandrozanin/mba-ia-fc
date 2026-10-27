# Execução da skill — projeto 2 (ecommerce-api-legacy)

Registro da execução real de `/refactor-arch` em sessão nova do Claude Code, com o projeto no estado original (tag `original-projects`) e a skill copiada em `.claude/skills/refactor-arch/`. Sessão `9af2ee44-9852-4ce7-9b2a-aa61b8fcc881`.

## Fases 1 e 2

Comando, executado dentro de `projects/ecommerce-api-legacy`:

```bash
claude -p "/refactor-arch Salve o relatório da Fase 2 em audit-report.md, na raiz deste projeto."
```

Saída da sessão (8 turnos). A skill parou no gate sem alterar código; o relatório completo está em `reports/audit-project-2.md`.

---

Terminei as Fases 1 e 2 e salvei o relatório em `audit-report.md`, na raiz do projeto. Não alterei nenhum código, configuração ou dado da aplicação.

## Fase 1 — Análise
- **Stack:** Node.js v24 com Express 4.22.1 e SQLite (pacote `sqlite3` 5.1.7). O banco fica em memória e é criado com dados iniciais a cada vez que a aplicação sobe.
- **Domínio:** uma plataforma de cursos com checkout: compra de curso (pagamento simulado e matrícula), relatório financeiro e exclusão de usuário.
- **Arquitetura:** tudo está concentrado em um único arquivo. A classe `AppManager` cuida de banco, rotas e regras de negócio; `src/utils.js` mistura configuração, segredos, cache e o "hash" de senha.
- **Endpoints:** `POST /api/checkout`, `GET /api/admin/financial-report`, `DELETE /api/users/:id`.
- **Escopo:** analisei os 3 arquivos-fonte e deixei de fora `node_modules` e `package-lock.json`. O projeto **não tem testes**. A aplicação sobe com `npm start`, na porta 3000.

## Fase 2 — Resumo da auditoria
| Severidade | Qtd |
|---|---:|
| CRITICAL | 3 |
| HIGH | 5 |
| MEDIUM | 4 |
| LOW | 3 |
| **Total** | **15** |

**Principais achados:**
- **CRITICAL:**
  - Senha do banco e chave do gateway de pagamento escritas direto no código (`src/utils.js:2-5`).
  - O número completo do cartão e a chave do gateway vão para o log a cada compra (`src/AppManager.js:45`).
  - A classe `AppManager` faz tudo sozinha: banco, rotas, pagamento, auditoria e relatório.
- **HIGH:**
  - O "hash" de senha depende só dos primeiros caracteres da senha, e quem não informa senha recebe `"123456"`.
  - As regras de negócio estão dentro das rotas.
  - O checkout grava em várias tabelas sem transação. Por isso, quando o pagamento é recusado, o usuário novo continua criado.
  - O relatório financeiro e a exclusão de usuário não exigem autenticação.
  - A exclusão de usuário deixa matrículas e pagamentos órfãos, ignora erros e sempre responde 200.
- **MEDIUM:**
  - Um cache global cresce sem limite e nunca é lido.
  - O relatório faz uma consulta por item (N+1): `1 + C + 2·E` consultas, onde C é o número de cursos e E o de matrículas.
  - Erros são tratados de forma opaca, e em dois casos derrubam o processo inteiro:
    - quando falha a consulta da linha 92;
    - quando `card` chega como número em vez de texto, pois `cc.startsWith` lança erro.
  - Os dados de entrada não são validados.
- **LOW:**
  - Há código morto.
  - Os nomes de variáveis são obscuros, como `u`, `e`, `cc`.
  - Há valores fixos sem nome, como `'PAID'` e o prefixo `"4"` que decide se o pagamento é aprovado.

Não encontrei APIs deprecated nas versões instaladas. Também não rodei `npm audit`, então o relatório não aponta vulnerabilidades conhecidas nas dependências.

Uma decisão precisa ser tomada antes da Fase 3: a autenticação das rotas de admin e de exclusão depende de um mecanismo que o projeto ainda não tem.

**Aprova a Fase 3 (refatoração para MVC)? (sim/não)** Se aprovar, diga também como prefere tratar a autenticação: implementar um mecanismo simples, por exemplo um token de admin vindo de variável de ambiente, ou deixar esse item fora do escopo.

---

## Aprovação (gate da Fase 2)

Depois da revisão humana dos relatórios, a mesma sessão foi retomada com:

```bash
claude -p --resume 9af2ee44-9852-4ce7-9b2a-aa61b8fcc881 "sim, aprovo a Fase 3. Para a autenticação das rotas admin e de exclusão, implemente um token de admin vindo de variável de ambiente."
```

## Fase 3

Saída da sessão (34 turnos):

---

Terminei a Fase 3: a API agora segue uma estrutura MVC, e as rotas de admin e de exclusão exigem um token de admin lido da variável de ambiente `ADMIN_TOKEN`. Os 12 testes novos passam (`npm test`) e a aplicação subiu e respondeu às mesmas requisições do baseline. Não fiz commit.

**O que foi verificado:**
- **Baseline do código original:** registrei status e corpo de cada endpoint. Também confirmei o crash: enviar `card` como número derrubou o processo.
- **Testes:** usam só ferramentas nativas do Node (`node:test`), sem dependências novas. Cobrem:
  - checkout com sucesso e pagamento recusado (que não deixa mais usuário criado);
  - entradas inválidas;
  - desfazer todas as gravações quando um passo do checkout falha;
  - resposta 401 sem token;
  - formato do relatório;
  - exclusão em cascata;
  - checkouts simultâneos.
- **Aplicação rodando:**
  - Sem `ADMIN_TOKEN`, ela se recusa a subir.
  - Com o token, checkout de sucesso, pagamento recusado e relatório devolvem as mesmas respostas de antes.
  - As rotas de admin sem token respondem 401.
  - `card` numérico responde 400 e o servidor continua de pé.
  - O log não mostra mais o número do cartão nem a chave do gateway.

**Estrutura nova:** `AppManager.js` e `utils.js` foram removidos. No lugar deles há `config/`, `db/`, `models/`, `services/`, `controllers/`, `routes/` e `middlewares/`, com `src/app.js` montando tudo. O token vai no cabeçalho `Authorization: Bearer <ADMIN_TOKEN>`, e `api.http` e o README já mostram isso.

**Mudanças de comportamento que você precisa conhecer:**
- `npm start` agora exige `ADMIN_TOKEN`.
- **Exclusão de usuário:** remove também as matrículas e os pagamentos dele, então a receita dessa pessoa sai do relatório. A mensagem de sucesso mudou, e agora responde 404 para usuário inexistente e 400 para id inválido.
- **Checkout:** passa a recusar com 400:
  - cartão fora de 12 a 19 dígitos;
  - e-mail sem formato válido;
  - usuário novo sem `pwd`.
- **Ordem da validação:** como a validação vem antes da busca do curso, `c_id` inexistente junto com cartão inválido dá 400, não 404.
- **Erros de banco:** passam a responder 500 em vez de 404 ou de um falso sucesso.

**Limitações:**
- **Pagamento:** continua simulado. Cartões que começam com `4` são aprovados.
- **Transações:** são feitas uma de cada vez numa única conexão SQLite. Leituras de outras requisições ainda podem enxergar dados de uma transação que ainda não foi concluída.
- **Login:** não existe, então a verificação de senha só é exercitada pelos testes.
- **Dependências:** não rodei `npm audit`.
- **Credenciais antigas:** continuam no histórico do git. Se forem reais, troque-as.

O `audit-report.md` agora tem também a seção da Fase 3, com baseline, estrutura antes e depois, o que foi feito em cada achado e os resultados.

---
