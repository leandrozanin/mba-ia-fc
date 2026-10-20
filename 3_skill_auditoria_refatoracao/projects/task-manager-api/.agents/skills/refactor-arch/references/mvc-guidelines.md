# Guidelines de arquitetura MVC

## Responsabilidades

- **Models:** representam e persistem dados; encapsulam consultas e invariantes diretamente relacionadas ao modelo. Não leem `request`, não constroem respostas HTTP e não guardam configuração global.
- **Views/Routes:** adaptam HTTP para a aplicação: métodos, paths, parsing de entrada, chamada ao controller e serialização/status da resposta. Não contêm SQL nem workflows extensos. Em APIs REST, “view” é a camada de apresentação/rota, não necessariamente HTML.
- **Controllers:** coordenam o caso de uso, chamam models e, quando o domínio exigir, serviços coesos; controlam o fluxo sem conhecer detalhes de transporte além do contrato definido pelo projeto. Evite controllers monolíticos.
- **Configuração:** centralize carregamento e validação de configuração; secrets vêm do ambiente/secret manager, nunca de valores versionados.
- **Composição/entry point:** constrói app, configura extensões/middlewares, registra rotas e inicia servidor apenas quando executado diretamente.
- **Middleware/error handler:** centralize tratamento de erro e logging seguro; preserve códigos HTTP e formato de erro existentes quando o contrato assim exigir.

## Direção das dependências

`Routes/Views → Controllers → Models/Services → DB ou integrações`. Os componentes internos não importam o objeto global da aplicação nem dependem de `request`. Injete conexões/configuração quando isso reduzir estado compartilhado e facilitar testes. Não crie abstrações sem necessidade demonstrada.

## Mapeamento por stack

- Flask: Blueprints para rotas, factory `create_app`, controllers/services Python, modelos/repositories e configuração validada.
- Express: routers para rotas, controllers de aplicação, models/repositories, middleware central e composition root.
- Outras stacks: mantenha a mesma separação conceitual usando o mecanismo idiomático do framework detectado.

## Compatibilidade

Antes de mover módulos, inventarie imports, scripts de inicialização, tabelas, métodos, paths, status e payloads. Prefira migrações incrementais. Não renomeie endpoint, coluna ou campo público sem autorização e plano de compatibilidade.
