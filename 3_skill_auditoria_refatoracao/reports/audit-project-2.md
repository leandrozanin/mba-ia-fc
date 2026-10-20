# Relatorio de Auditoria — Projeto 2: ecommerce-api-legacy

## Analise do projeto
- Linguagem/framework: JavaScript / Node.js 22.22.3 e Express 4.18.2.
- Banco: SQLite em memoria via `sqlite3`.
- Dominio: LMS com cursos, matriculas, pagamentos e checkout.
- Arquitetura: `app.js` compoe o servidor; `AppManager.js` cria schema, registra rotas, executa casos de uso e monta relatorio; `utils.js` contem configuracao e estado global.
- Arquivos-fonte analisados: 3 (`src/app.js`, `src/AppManager.js`, `src/utils.js`).
- Baseline: servidor iniciou; `GET /api/admin/financial-report` e checkout de teste responderam 200.
- Dependencias: `npm ci` concluiu. `npm audit` em 2026-10-19 reportou 14 vulnerabilidades: 2 critical, 8 high, 1 moderate e 3 low.

## Resumo
| Severidade | Quantidade |
|---|---:|
| CRITICAL | 2 |
| HIGH | 1 |
| MEDIUM | 2 |
| LOW | 2 |
| **Total** | **7** |

## Achados

### [CRITICAL] Credenciais fixas e dados de pagamento em logs
- **Local:** `src/utils.js:2-6` e `src/AppManager.js:45`
- **Evidencia:** configuracao contem credenciais/token literais; checkout registra o numero de cartao e a chave do gateway.
- **Impacto:** comprometimento de integracoes e exposicao de dados financeiros em logs.
- **Recomendacao:** remover/rotacionar secrets se reais, carregar de ambiente/secret store e redigir logs de pagamento.

### [CRITICAL] Dependencias com vulnerabilidades criticas e altas
- **Local:** `package-lock.json:1563-2113` (entradas transitivas)
- **Evidencia:** `npm audit` encontrou 14 vulnerabilidades no grafo bloqueado, incluindo `proxy-addr` e `tar` critical e `sqlite3` e outros pacotes high.
- **Impacto:** componentes vulneraveis podem aumentar a superficie de ataque.
- **Recomendacao:** revisar avisos detalhados, atualizar dependencias de forma controlada e rodar testes; nao aplicar `npm audit fix --force` sem verificar breaking changes.

### [HIGH] AppManager concentra infraestrutura e casos de uso
- **Local:** `src/AppManager.js:6-141`
- **Evidencia:** a classe cria tabelas/seeds, registra endpoints, processa checkout e agrega relatorio.
- **Impacto:** testes isolados e manutencao ficam dificeis.
- **Recomendacao:** separar routers, controllers, models/repositorios e servicos de checkout/relatorio; manter `app.js` como composition root.

### [MEDIUM] Consultas N+1 no relatorio financeiro
- **Local:** `src/AppManager.js:89-120`
- **Evidencia:** loop de cursos consulta matriculas; dentro dele, loop de matriculas consulta usuario e pagamento.
- **Impacto:** tempo de resposta aumenta com o volume.
- **Recomendacao:** agregar com JOIN/consultas em lote e testar o resultado.

### [MEDIUM] Checkout pode deixar escrita parcial
- **Local:** `src/AppManager.js:50-82`
- **Evidencia:** matricula, pagamento e audit log sao escritos em etapas distintas sem transacao envolvendo o conjunto.
- **Impacto:** uma falha intermediaria pode deixar estado inconsistente.
- **Recomendacao:** envolver fluxo em transacao, com rollback e teste de falha intermediaria.

### [LOW] Estado mutavel global
- **Local:** `src/utils.js:9-10`
- **Evidencia:** cache e contador de receita vivem em variaveis de modulo.
- **Impacto:** isolamento de testes e previsibilidade entre instancias ficam prejudicados.
- **Recomendacao:** injetar servicos e remover estado sem uso.

### [LOW] Variavel morta e nomes abreviados
- **Local:** `src/utils.js:10` e `src/AppManager.js:29-33`
- **Evidencia:** `totalRevenue` nao e consultado; o handler usa abreviacoes para usuario, email, cartao e curso.
- **Impacto:** leitura e revisao do checkout ficam menos seguras.
- **Recomendacao:** remover variavel morta e usar nomes descritivos.

## APIs deprecated
Nenhuma API deprecated de Express/Node foi confirmada no codigo da aplicacao. `npm ci` tambem avisou sobre pacotes transitivos deprecated; isso e distinto de API chamada diretamente pelo projeto.

## Gate da Fase 2
A auditoria nao alterou a logica da aplicacao. Aprovar a Fase 3 para este projeto? Aguardar resposta explicita antes de alterar codigo, configuracao da aplicacao ou dados.
