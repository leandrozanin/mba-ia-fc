# Execução da skill — projeto 3 (task-manager-api)

Registro da execução real de `/refactor-arch` em sessão nova do Claude Code, com o projeto no estado original (tag `original-projects`) e a skill copiada em `.claude/skills/refactor-arch/`. Sessão `f37b6cea-e659-48f7-8e00-d2d60c9fa618`.

## Fases 1 e 2

Comando, executado dentro de `projects/task-manager-api`:

```bash
claude -p "/refactor-arch Salve o relatório da Fase 2 em audit-report.md, na raiz deste projeto."
```

Saída da sessão (33 turnos). A skill parou no gate sem alterar código; o relatório completo está em `reports/audit-project-3.md`.

---

Salvei o relatório da Fase 2 em `audit-report.md`, na raiz do projeto. Foi o único arquivo criado; o código, a configuração e os dados não foram alterados.

**Fase 1, em resumo:** é uma API de tarefas em Python 3.12 com Flask 3.0 e SQLite (Flask-SQLAlchemy 3.1.1; SQLAlchemy 2.1.6 instalado, mas sem versão fixada). Tem 22 endpoints e segue um MVC só parcial: as rotas fazem validação, regra de negócio e acesso ao banco, e o código em `services/` e a maior parte de `utils/` não é usado. Analisei 15 arquivos `.py`, deixando de fora `.venv/` e `.claude/`. O projeto não tem testes; para subir, roda `python seed.py` e depois `python app.py`.

**Fase 2: 19 achados**

| Severidade | Qtde | Principais |
|---|---:|---|
| CRITICAL | 3 | Segredos no código (`SECRET_KEY` em `app.py:13` e login/senha SMTP em `services/notification_service.py:9-10`); hash da senha devolvido no JSON (`models/user.py:21`); nenhuma autenticação, com token falso e qualquer pessoa podendo criar um `admin` |
| HIGH | 4 | Senhas em MD5 sem salt; `debug=True` com `host='0.0.0.0'`; regra de negócio e acesso ao banco dentro das rotas; `app` global sem factory, com `create_all` rodando no import |
| MEDIUM | 8 | CORS aberto para qualquer origem; excluir uma categoria deixa tarefas apontando para ela; consultas N+1; regras duplicadas e inconsistentes; tipos de entrada sem validação (vira 500 em vez de 400); `except:` genérico; `Query.get()` deprecated (16 chamadas); `datetime.utcnow()` deprecated no Python 3.12 |
| LOW | 4 | Valores fixos espalhados pelo código; código morto e imports sem uso; `print` no lugar de logging; CRUD de categorias dentro do blueprint de relatórios |

A auditoria foi só estática: não subi a aplicação. Os casos de erro 500 foram deduzidos lendo o código, sem testar por requisição real, e não rodei nenhum scanner de vulnerabilidades nas dependências.

**Você aprova a Fase 3 (refatoração)? (sim/não)** Até você responder, não mexo em nada.

---

## Aprovação (gate da Fase 2)

Depois da revisão humana dos relatórios, a mesma sessão foi retomada com:

```bash
claude -p --resume f37b6cea-e659-48f7-8e00-d2d60c9fa618 "sim, aprovo a Fase 3."
```

## Fase 3

Saída da sessão (72 turnos):

---

A Fase 3 terminou: os 53 testes novos passam, a aplicação sobe normalmente e os 22 endpoints responderam com o status esperado em requisições HTTP reais. Não fiz commit; as mudanças estão no working tree.

**Correção no relatório.** Antes de mexer no código, registrei o comportamento original: o projeto não tinha testes, então rodei 56 requisições contra uma cópia isolada, com banco SQLite temporário. Isso mostrou que um achado da Fase 2 estava errado. Excluir uma categoria **não** deixa tarefas apontando para uma categoria inexistente: o SQLAlchemy zera o `category_id` delas automaticamente. Removi esse achado (o total passou de 19 para 18) e registrei o erro numa errata no `audit-report.md`.

**O que foi validado**
| Verificação | Resultado |
|---|---|
| `python -m unittest discover -s tests -t .` | 53 testes OK |
| As mesmas 56 requisições, antes e depois | 46 respostas idênticas; as 10 diferentes mudaram de propósito |
| Requisições rodando com `DeprecationWarning` tratado como erro | nenhum aviso |
| `seed.py` + `app.py` + os 22 endpoints via `curl` | todos com o status esperado |
| Boot sem `SECRET_KEY` | a aplicação se recusa a subir |

**Nova estrutura:** `app.py` (`create_app` e tratamento central de erros) → `routes/` (só HTTP: autenticação e formato das respostas) → `controllers/` (casos de uso, validação, commit e rollback) → `models/` (dados, constantes e a regra de tarefa atrasada num só lugar) e `services/` (token e e-mail). A configuração fica em `config.py`, lida do ambiente (`.env.example`).

**O que mudou para quem usa a API**
- **Login obrigatório para escrever:** criar, editar e apagar tarefas, categorias e usuários agora exige `Authorization: Bearer <token>`. Clientes atuais vão receber 401 até mandarem o token.
- **Token:** `/login` devolve um token assinado e com validade. O formato antigo `fake-jwt-token-N` é rejeitado.
- **Permissões:** só administradores criam outros admins, mudam papel ou status e apagam usuários. Um usuário comum só edita o próprio cadastro.
- **Senhas:**
  - o campo `password` não aparece mais em nenhuma resposta;
  - o MD5 foi trocado pelo hash com salt do werkzeug;
  - quem tem hash antigo continua entrando, e o hash é convertido no login;
  - a senha mínima subiu de 4 para 8 caracteres.
- **Entrada inválida:** os 4 casos que davam erro 500 em HTML agora devolvem 400 em JSON.
- **Servidor e CORS:** debug desligado, só `127.0.0.1` por padrão, e CORS desligado enquanto `CORS_ORIGINS` não for definido.
- **Mensagens de erro:** o texto de data inválida no `PUT /tasks` agora é igual ao do `POST`.

Nas demais respostas, o formato JSON ficou igual, incluindo as estatísticas e os relatórios. O `/health` passou a mostrar a hora em UTC em vez da hora local.

**Limitações**
- As rotas `GET` continuam públicas, inclusive os e-mails em `/users`, para não quebrar quem só lê.
- `NotificationService` agora lê as credenciais da configuração, mas nenhuma rota usa esse serviço.
- `marshmallow` e `requests` continuam declarados sem uso, e não rodei `pip-audit` nas dependências.
- Não há limite de tentativas no `/login`.
- As senhas de exemplo do `seed.py` continuam curtas.

O README e o `audit-report.md` foram atualizados com os comandos, os resultados e essas limitações.

---
