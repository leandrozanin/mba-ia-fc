# Execução da skill — projeto 1 (code-smells-project)

Registro da execução real de `/refactor-arch` em sessão nova do Claude Code, com o projeto no estado original (tag `original-projects`) e a skill copiada em `.claude/skills/refactor-arch/`. Sessão `c1e6a04c-cb37-4d9e-9905-aa0b49b9f6bd`.

## Fases 1 e 2

Comando, executado dentro de `projects/code-smells-project`:

```bash
claude -p "/refactor-arch Salve o relatório da Fase 2 em audit-report.md, na raiz deste projeto."
```

Saída da sessão (16 turnos). A skill parou no gate sem alterar código; o relatório completo está em `reports/audit-project-1.md`.

---

Salvei o relatório de auditoria da Fase 2 em `audit-report.md`, na raiz do projeto. Não alterei nenhum código, configuração ou dado. Nada foi executado: as linhas citadas foram conferidas lendo o código, sem rodar a aplicação nem testar os ataques. O projeto não tem testes.

**O projeto:** uma API de e-commerce em Python 3.12 e Flask 3.1.1, com SQLite e 4 arquivos de código (780 linhas). A organização é só parcialmente MVC e tem 20 rotas.

| Severidade | Quantidade |
|---|---:|
| CRITICAL | 4 |
| HIGH | 6 |
| MEDIUM | 4 |
| LOW | 4 |
| **Total** | **18** |

**CRITICAL:**
- **Injeção de SQL em quase todas as queries de `models.py`:** o login em `models.py:110` aceita entrada sem senha válida.
- **Rotas administrativas abertas:** `/admin/query` executa SQL arbitrário e `/admin/reset-db` apaga o banco, ambas sem nenhuma checagem de acesso.
- **Chave secreta do Flask no código:** está em `app.py:7` e o `/health` devolve esse valor na resposta.
- **Senhas em texto puro:** são gravadas sem hash e devolvidas pelo `GET /usuarios`.

**HIGH:**
- Nenhuma rota exige login ou checa permissão.
- O app sobe com `debug=True` em `0.0.0.0` e aceita chamadas de qualquer site (CORS aberto).
- A criação de pedido não usa transação: uma falha no meio pode deixar pedido incompleto, e duas compras ao mesmo tempo podem vender acima do estoque. Cancelar um pedido não devolve o estoque.
- Todas as requisições compartilham uma única conexão com o banco.
- Há SQL direto nas rotas, e regras de negócio ficam na camada de dados.

**MEDIUM:** consultas repetidas em loop na listagem de pedidos (N+1). Falta validação de entrada; o caso mais sério é que uma quantidade negativa no pedido aumenta o estoque e gera total negativo. A validação de criar e atualizar produto é diferente entre si, e os erros devolvem a mensagem interna do sistema.

**LOW:** logs com `print` que incluem e-mails, valores fixos espalhados pelo código, imports não usados e trechos duplicados.

Não encontrei nenhuma API deprecated nas versões usadas pelo projeto.

**Aprova a Fase 3 (refatoração MVC)?** Responda sim ou não. Sem aprovação, encerro aqui.

---

## Aprovação (gate da Fase 2)

Depois da revisão humana dos relatórios, a mesma sessão foi retomada com:

```bash
claude -p --resume c1e6a04c-cb37-4d9e-9905-aa0b49b9f6bd "sim, aprovo a Fase 3."
```

## Fase 3

Saída da sessão (57 turnos):

---

A Fase 3 está concluída: a aplicação foi reorganizada em MVC e os 18 achados do relatório foram tratados. Os 30 testes novos passam, e o smoke test HTTP contra o servidor real, iniciado com `python app.py`, mostra os comportamentos esperados. Nada foi commitado.

## Como validei
- **Baseline:** rodei uma cópia do app original numa pasta temporária, para o `loja.db` não ser criado dentro do projeto, e exercitei todos os endpoints com um script. Os problemas do relatório se confirmaram na prática: o login com SQL injection devolveu 200, um apóstrofo no nome do produto deu 500, uma quantidade negativa aumentou o estoque (50→51), cancelar um pedido não devolveu o estoque e o `/health` expunha a chave secreta.
- **Depois:** o mesmo script contra a versão nova, também com banco temporário. Agora a injeção devolve 401 e a busca maliciosa retorna 0 resultados. O produto com apóstrofo é criado normalmente. O estoque vai de 50 para 48 com o pedido e volta a 50 no cancelamento. O `/health` não mostra mais configuração, `/admin/query` deixou de existir e o servidor sobe em `127.0.0.1` com debug desligado.
- **Testes:** `python -m unittest discover -s tests -t . -v`, 30 testes sem nenhuma dependência nova.
- **Outras checagens:** sem `SECRET_KEY` o app recusa iniciar com uma mensagem clara. Não sobrou nenhuma senha ou segredo fixo no código.

## Estrutura antes e depois
- **Antes:** `app.py` (rotas e SQL de admin), `controllers.py`, `models.py` (SQL concatenado) e `database.py` (conexão global).
- **Depois:** o pacote `loja/`, que separa rotas (Blueprints), controllers sem dependência de `request`, models com SQL parametrizado, validação, autenticação, permissões, notificador e configuração lida do ambiente. A criação do app fica numa função `create_app`, cada requisição usa a própria conexão com o banco e a criação de pedido roda numa transação única. Os três arquivos antigos foram removidos e continuam recuperáveis pelo git. O README foi atualizado.

## Mudanças que afetam quem usa a API
Os caminhos, os campos e as mensagens de sucesso continuam iguais. Mudou isto:
- **Login obrigatório:** criar pedido exige token, e listar usuários, pedidos e relatório, além de criar ou alterar produtos, exigem um usuário administrador. O `POST /login` agora devolve um `token`, para enviar no cabeçalho `Authorization: Bearer <token>`.
- **Senhas:** deixaram de aparecer nas respostas.
- **Erros:** e-mail duplicado devolve 409. Erros de validação devolvem 400 em vez de 500. Pedido inexistente devolve 404, e um pedido cancelado não pode mais mudar de status.
- **Admin:** `/admin/query` foi removida. `/admin/reset-db` só funciona com `ENABLE_ADMIN_RESET` ligado e um administrador logado.
- **Configuração no boot:** é preciso definir `SECRET_KEY`. CORS vem desligado e só é liberado listando as origens em `CORS_ORIGINS`.
- **Usuários de exemplo:** o banco não é mais criado com os três usuários de exemplo e suas senhas. O administrador inicial vem de `ADMIN_EMAIL` e `ADMIN_PASSWORD`. Bancos antigos continuam funcionando: no boot, as senhas guardadas sem criptografia são convertidas para hash.

## Limitações
- A proteção contra duas compras simultâneas do mesmo produto não foi testada com carga real. Os testes cobrem o rollback numa falha no meio do pedido e o estoque insuficiente sem deixar gravação parcial.
- Não há política de senha forte nem limite de tentativas de login.
- O servidor embutido do Flask continua sendo só para desenvolvimento; em produção é preciso um servidor WSGI.
- Se um banco antigo já tiver e-mails duplicados, o índice de e-mail único não é criado. Nesse caso a unicidade só é garantida pela própria aplicação, que registra um aviso no log.
- As notificações de e-mail, SMS e push continuam sem integração real. Agora só registram o evento no log, mas o notificador pode ser trocado por uma implementação real.

As saídas completas do baseline e do teste depois da refatoração estão em:
- `C:\Users\leand\AppData\Local\Temp\claude\C--Users-leand-rarch-orig-3-skill-auditoria-refatoracao-projects-code-smells-project\c1e6a04c-cb37-4d9e-9905-aa0b49b9f6bd\scratchpad\baseline-smoke.txt`
- `C:\Users\leand\AppData\Local\Temp\claude\C--Users-leand-rarch-orig-3-skill-auditoria-refatoracao-projects-code-smells-project\c1e6a04c-cb37-4d9e-9905-aa0b49b9f6bd\scratchpad\after-smoke.txt`

---
