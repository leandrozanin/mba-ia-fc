# Catálogo de anti-patterns

A severidade mede impacto comprovado no contexto da aplicação. Não classifique apenas pelo nome do padrão; cite a evidência no código.

| Severidade | Anti-pattern | Sinais para detectar | Direção de correção |
|---|---|---|---|
| CRITICAL | Segredos embutidos | Chaves, senhas, tokens ou credenciais fixas em código/configuração versionada | Remover, rotacionar quando real, obter de ambiente/secret store e evitar log |
| CRITICAL | SQL injection / execução arbitrária | Query montada com entrada, concatenação/interpolação SQL ou endpoint que executa SQL arbitrário | Parâmetros preparados, allowlist de operações e remoção de endpoint administrativo exposto |
| CRITICAL | God class / god method | Um módulo concentra roteamento, regras de vários domínios, persistência e integração | Separar responsabilidades em unidades coesas com limites explícitos |
| HIGH | Regra de negócio no handler/route | Cálculos, transações ou workflows complexos dentro de rotas/controllers | Delegar para controller/serviço de aplicação e deixar a rota como adaptador HTTP |
| HIGH | Acoplamento rígido / estado global mutável | Singleton global de DB/cache, configuração mutada em runtime, dependência concreta espalhada | Injetar dependências e controlar ciclo de vida por aplicação/request |
| HIGH | Persistência ou segredo na camada de apresentação | SQL, acesso ao driver, autenticação ou política de autorização dentro de view/route | Delegar persistência ao model/repository e política ao componente de aplicação adequado |
| HIGH | Falta de controle transacional | Escritas parciais em workflow de múltiplas tabelas; falhas deixam estoque/saldo inconsistente | Transação atômica, rollback e testes de falha intermediária |
| MEDIUM | Query N+1 | Consulta adicional dentro de loop de entidades relacionadas | Join, eager loading, agregação ou lote de IDs |
| MEDIUM | Validação duplicada/inconsistente | Mesma regra copiada entre create/update/rotas, com resultados diferentes | Schema/validador compartilhado e erros coerentes |
| MEDIUM | Falta de validação de entrada | Tipos, limites, enumerações ou relações são usados sem validação previsível | Validar na fronteira e rejeitar entrada inválida com resposta adequada |
| MEDIUM | Tratamento de erro opaco | `except`/callback engole erro, retorna sucesso falso ou expõe exceções internas | Tratar classes esperadas, log seguro e resposta HTTP consistente |
| MEDIUM | API deprecated | Chamada marcada obsoleta pela documentação da versão em uso, por exemplo `Query.get()` legado ou `datetime.utcnow()` no Python 3.12+ | Confirmar versão e contexto, apontar equivalente moderno e migrar com teste |
| LOW | Magic numbers/strings | Limites, estados ou defaults repetidos sem nome ou domínio explícito | Constantes/enums locais com nome e significado |
| LOW | Código morto/imports não usados | Símbolos não referenciados, duplicações sem efeito ou branch inalcançável | Remover após confirmar ausência de uso/reflexão |
| LOW | Logging improvisado/nomenclatura obscura | `print`, nomes de uma letra ou logs com informação operacional/sensível | Logger estruturado, nomes claros e remoção de payloads sensíveis |

## Regras de evidência

- Mostre linhas de código relevantes, não a linha da declaração da classe por conveniência.
- Uma dependência vulnerável deve ser checada com dados atuais antes de alegar CVE; findings estáticos não substituem `npm audit`/scanner.
- “Deprecated” exige referência à documentação da versão da dependência/runtime do projeto. Não inferir pela idade ou preferência pessoal.
- Diferencie risco explorável de oportunidade de manutenção; a severidade não deve inflar por dramatização.
