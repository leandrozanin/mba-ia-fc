# Pull, otimização e avaliação de prompts com LangSmith

Este projeto busca um prompt inicial do LangSmith Prompt Hub, converte relatos de bugs em user stories usando um prompt versionado em YAML e avalia as respostas no dataset de 15 casos. O fluxo usa os padrões de pull/push e de avaliação apresentados nos exemplos de `conteudo/mba-ia-prompt-engineering-main`.

## Técnicas aplicadas (Fase 2)

O prompt v2 combina três técnicas, registradas também em `techniques_applied` no YAML:

- **Role Prompting:** define a persona de Product Manager sênior para orientar a linguagem e manter o foco no valor para quem usa o produto.
- **Few-shot Learning:** inclui três exemplos de entrada e saída para bugs simples, de validação e de segurança. Os exemplos mostram a estrutura esperada sem depender de instruções vagas.
- **Skeleton of Thought:** determina uma estrutura previsível para história, critérios de aceitação e, quando houver dados no relato, contexto técnico. Isso ajuda a cobrir bugs complexos sem misturar sintomas e critérios.

O prompt também pede uma análise interna sem expor raciocínio passo a passo, exige critérios testáveis e orienta a preservar fatos e evitar requisitos inventados.

## Requisitos

- Python 3.10+
- Uma conta e uma API key do LangSmith
- Uma API key de um provedor de LLM: OpenAI ou Google Gemini
- Um handle público do LangSmith Prompt Hub

O handle é criado na interface do LangSmith quando você torna um prompt público pela primeira vez. Depois de escolhido, informe-o em `USERNAME_LANGSMITH_HUB` no `.env`.

## Configuração

Abra um terminal nesta pasta. No Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

No macOS ou Linux, ative o ambiente com `source .venv/bin/activate` e crie o arquivo de configuração com `cp .env.example .env`.

Edite `.env` e preencha:

```dotenv
LANGSMITH_API_KEY=sua-chave-langsmith
LANGSMITH_PROJECT=mba-ia-pull-evaluation-prompt
USERNAME_LANGSMITH_HUB=seu-handle-publico

LLM_PROVIDER=openai
LLM_MODEL=modelo-para-gerar-respostas
EVAL_MODEL=modelo-para-avaliar
OPENAI_API_KEY=sua-chave-openai
```

Para Gemini, use `LLM_PROVIDER=google`, preencha `GOOGLE_API_KEY` e escolha modelos disponíveis para `LLM_MODEL` e `EVAL_MODEL`. O `.env.example` contém links para os catálogos oficiais. `LANGSMITH_PROJECT` também define o nome do dataset como `<projeto>-eval`. Mantenha `LANGSMITH_TRACING=true` para registrar os traces.

## Como executar

Rode os comandos a partir da raiz desta pasta, com o ambiente virtual ativado.

1. Baixe o prompt inicial público do desafio e grave-o em `prompts/bug_to_user_story_v1.yml`:

   ```powershell
   python src/pull_prompts.py
   ```

   O pull usa `dangerously_pull_public_prompt=True` para o prompt público especificado na spec. A versão local incluída serve como referência caso você não tenha credenciais configuradas ainda.

2. Revise ou edite `prompts/bug_to_user_story_v2.yml`. O `user_prompt` precisa manter a variável `{bug_report}`, usada pelos exemplos do dataset.

3. Publique o prompt v2 como público no seu handle:

   ```powershell
   python src/push_prompts.py
   ```

4. Rode a avaliação no dataset original de 15 exemplos:

   ```powershell
   python src/evaluate.py
   ```

   Cada avaliação cria um experimento no LangSmith e grava as métricas Helpfulness, Correctness, F1-Score, Clarity e Precision. O critério de aprovação exige que cada métrica e a média sejam pelo menos 0,8. O avaliador chama o provedor para cada resposta e métrica; configure limites e faturamento da API antes de rodar.

5. Se alguma métrica ficar abaixo de 0,8, ajuste somente o prompt v2, publique novamente e avalie outra vez. O dataset fornecido não deve ser alterado.

## Testes locais

Os seis testes de formato do prompt não usam LangSmith nem chamam modelos:

```powershell
pytest tests/test_prompts.py
```

## Resultados finais e evidências

As métricas reais dependem da execução com suas chaves e do experimento criado no seu workspace. Não há notas ou link de experimento registrados neste repositório ainda. Após uma avaliação aprovada, compartilhe o dataset para criar um link público:

```python
from langsmith import Client

client = Client()
print(client.share_dataset(dataset_name="<LANGSMITH_PROJECT>-eval")["url"])
```

Inclua no repositório o link compartilhado e capturas de tela do dashboard mostrando os 15 exemplos, as notas aprovadas e traces de pelo menos três casos. Compare no dashboard os runs da v1 e da v2 para documentar as melhorias observadas.

## Estrutura principal

- `prompts/bug_to_user_story_v1.yml`: prompt semente local; pode ser atualizado pelo script de pull.
- `prompts/bug_to_user_story_v2.yml`: prompt otimizado e versionado.
- `datasets/bug_to_user_story.jsonl`: dataset original de avaliação com 15 exemplos.
- `src/pull_prompts.py` e `src/push_prompts.py`: integração com o Prompt Hub.
- `src/evaluate.py`, `src/metrics.py` e `src/utils.py`: avaliação, métricas e funções auxiliares fornecidas pelo projeto base.
- `tests/test_prompts.py`: validações do prompt v2.
