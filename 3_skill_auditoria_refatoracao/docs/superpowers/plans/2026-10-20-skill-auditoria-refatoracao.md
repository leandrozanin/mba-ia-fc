# Skill de Auditoria e Refatoração MVC — Plano de Implementação

> **Para agentes de implementação:** executar tarefa por tarefa com TDD quando houver comportamento testável, validar cada etapa e registrar decisões.

**Objetivo:** entregar no diretório `3_skill_auditoria_refatoracao` a skill `refactor-arch` para Codex, as análises manuais, os relatórios e os três projetos refatorados conforme a spec.

**Arquitetura:** obter os três projetos do repositório público indicado pela spec e mantê-los em `projects/`. Criar a skill Codex em `.agents/skills/refactor-arch/`, com `SKILL.md` conciso e referências Markdown para análise, catálogo, relatório, MVC e refatoração. Executar auditoria e refatoração projeto por projeto; guardar evidências e relatórios em `reports/`.

**Stack:** Codex Agent Skills, Markdown, Python/Flask, Node.js/Express e ferramentas de teste já presentes em cada projeto.

**Spec:** `3_skill_auditoria_refatoracao/spec.md`.

## Restrições globais

- A skill deve cobrir Python/Flask e Node.js/Express e reconhecer projetos com e sem camadas existentes.
- A auditoria deve ter ao menos 8 anti-patterns nas severidades CRITICAL, HIGH, MEDIUM e LOW, incluindo APIs deprecated.
- O playbook deve conter ao menos 8 transformações com exemplos antes/depois.
- A Fase 2 deve apresentar relatório com caminhos e linhas exatos, ordenado por severidade, e aguardar aprovação antes de modificar código-alvo.
- A Fase 3 exige boot bem-sucedido e verificação dos endpoints existentes.
- Não alterar a pasta `conteudo/`.
- Os projetos-alvo não estão no checkout atual; obter do repositório público citado pela spec e registrar a origem.
- Respeitar dados e arquivos preexistentes; não sobrescrever alterações locais sem inspeção.

## Foco de revisão

- Credenciais e segredos que possam vazar em relatórios ou permanecer hardcoded após a refatoração.
- Migrações que mudem contratos de endpoints ou formatos de resposta.
- Compatibilidade entre versões instaladas e instruções de execução quando os manifestos/dependências estiverem ausentes ou ambíguos.
- Detecção de API deprecated sem falso positivo por comentários, documentação ou dependências não usadas.
- Falhas de boot/endpoints causadas por alterações de diretório de trabalho, imports ou configuração.

---

### Tarefa 1: Obter e inventariar os projetos-alvo

**Arquivos:** criar `projects/code-smells-project/`, `projects/ecommerce-api-legacy/` e `projects/task-manager-api/`; registrar origem em `README.md`.

- [ ] Obter o repositório base da URL indicada na spec, preservando os diretórios originais.
- [ ] Inventariar linguagens, arquivos-fonte, comandos de teste/boot e endpoints; guardar evidência inicial para comparação.
- [ ] Executar os testes/boots de baseline disponíveis e registrar falhas preexistentes.

### Tarefa 2: Análise manual e base documental

**Arquivos:** criar `README.md` em `3_skill_auditoria_refatoracao/`.

- [ ] Documentar por projeto ao menos cinco achados com severidade, arquivo/linha e justificativa; atender à distribuição mínima da spec.
- [ ] Documentar decisões, comportamento esperado da skill, resultados e comandos para uso no Codex.
- [ ] Validar que os achados correspondem ao código-fonte original e às linhas atuais.

### Tarefa 3: Skill Codex `refactor-arch`

**Arquivos:** criar `.agents/skills/refactor-arch/SKILL.md` e referências Markdown em `references/`.

- [ ] Escrever instruções sequenciais para análise, auditoria com pausa explícita e refatoração com validação.
- [ ] Escrever referências cobrindo heurísticas de stack/arquitetura, catálogo de no mínimo oito anti-patterns, template, responsabilidades MVC e playbook com oito exemplos antes/depois.
- [ ] Conferir que os nomes e links internos da skill resolvem e que o formato segue o padrão de Skills do Codex.
- [ ] Copiar a mesma skill para os outros dois projetos para demonstrar portabilidade.

### Tarefa 4: Auditoria dos três projetos

**Arquivos:** criar `reports/audit-project-1.md`, `reports/audit-project-2.md`, `reports/audit-project-3.md`.

- [ ] Aplicar as heurísticas e gerar relatórios com stack, domínio, contagem, findings ordenados, linha exata, impacto e recomendação.
- [ ] Conferir no mínimo cinco achados por projeto, incluindo CRITICAL ou HIGH em cada projeto, e comparar com a análise manual.
- [ ] Atualizar a seção de resultados no README com contagens por severidade e divergências observadas.
- [ ] Parar em cada relatório e solicitar aprovação antes de iniciar qualquer alteração no respectivo projeto, conforme requisito da Fase 2.

### Tarefa 5: Refatoração e validação por projeto

**Arquivos:** alterar os arquivos de cada `projects/*`; guardar logs de validação em `reports/`.

- [ ] Após aprovação do relatório do projeto, aplicar mudanças MVC proporcionais aos achados, mantendo contratos e dados compatíveis.
- [ ] Rodar testes, iniciar a aplicação e verificar os endpoints originais com os comandos adequados a cada stack.
- [ ] Registrar estrutura antes/depois, checklist preenchido e logs reais; não declarar critério como atendido sem evidência.
- [ ] Repetir auditoria/validação quando o primeiro ciclo indicar regressões ou cobertura insuficiente.

### Tarefa 6: Revisão final da entrega

**Arquivos:** atualizar README e evidências finais.

- [ ] Conferir a cobertura integral da spec, organização dos três projetos, cópias da skill e três relatórios.
- [ ] Rodar validações finais disponíveis e conferir `git diff` para excluir artefatos e alterações fora do escopo.
- [ ] Registrar limitações, especialmente qualquer endpoint que não possa ser exercitado sem serviço/credencial externa.
