---
name: refactor-arch
description: Analisa uma codebase, audita problemas arquiteturais e de qualidade e propõe uma refatoração MVC segura, com aprovação explícita antes de alterar código.
---

# Refactor Arch

Use esta skill quando pedirem análise arquitetural, auditoria de code smells ou refatoração MVC de um projeto.

Siga as três fases na ordem. Use `references/project-analysis.md`, `references/anti-pattern-catalog.md`, `references/audit-report-template.md`, `references/mvc-guidelines.md` e `references/refactoring-playbook.md` como fonte de procedimento e formato.

## Fase 1 — Análise

1. Inspecione manifestos, arquivos-fonte, pontos de entrada, testes, configuração e persistência. Ignore dependências vendorizadas, caches, builds e arquivos gerados.
2. Detecte linguagem, framework, bibliotecas, banco, domínio e arquitetura com evidência dos arquivos encontrados. Conte os arquivos-fonte analisados e informe as exclusões.
3. Apresente um resumo curto da stack, domínio, arquitetura atual, comandos de teste/boot e rotas/endpoints conhecidos. Não altere arquivos.

## Fase 2 — Auditoria

1. Compare o código-fonte com `references/anti-pattern-catalog.md`; investigue também APIs deprecated adequadas à stack.
2. Registre somente achados comprovados. Verifique cada caminho e linha no arquivo atual. Ordene por severidade CRITICAL, HIGH, MEDIUM e LOW; inclua descrição, evidência, impacto e recomendação.
3. Use `references/audit-report-template.md` e salve o relatório no caminho acordado com a pessoa solicitante.
4. Mostre contagens por severidade e achados. **Pare e peça aprovação explícita para a Fase 3. Não altere código, configuração ou dados da aplicação antes dessa aprovação.** Se a resposta não aprovar, encerre após o relatório.

## Fase 3 — Refatoração

Só comece depois da aprovação explícita do relatório da Fase 2.

1. Registre baseline: testes existentes, comando de boot e comportamento/status dos endpoints originais.
2. Aplique apenas transformações justificadas pelos achados, seguindo `references/mvc-guidelines.md` e `references/refactoring-playbook.md`. Preserve contratos HTTP e dados quando possível; extraia segredos para configuração externa e não os replique em logs ou relatórios.
3. Adicione ou atualize testes para os comportamentos alterados. Rode a suíte completa, inicie a aplicação e exercite os endpoints originais com requisições representativas. Em SQLite, use um banco temporário quando possível.
4. Corrija regressões e repita a validação. Relate comandos e resultados reais, estrutura antes/depois e limitações. Não declare endpoints ou findings resolvidos sem verificar o resultado.

## Limites

- Não invente stack, endpoints, métricas, linhas, resultados ou segurança.
- Se faltarem dependências, credenciais ou serviços necessários, informe o bloqueio e valide o que for possível sem expor segredos.
- Uma arquitetura já organizada ainda pode ter problemas de segurança, desempenho, validação ou responsabilidades; avalie o comportamento e as evidências, não apenas nomes de pastas.
