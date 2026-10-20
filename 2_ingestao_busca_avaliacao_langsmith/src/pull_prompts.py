"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull do prompt semente do desafio
3. Salva localmente em prompts/bug_to_user_story_v1.yml

DICAS DE IMPLEMENTAÇÃO:

- O pull é feito pelo cliente do LangSmith:

      from langsmith import Client
      client = Client()
      prompt = client.pull_prompt(
          "leonanluppi/bug_to_user_story_v1",
          dangerously_pull_public_prompt=True,
      )

- O parâmetro `dangerously_pull_public_prompt=True` é obrigatório sempre que o
  identificador tem dono explícito ("owner/nome"). O LangSmith bloqueia esse pull
  por padrão porque um prompt do Hub é um objeto LangChain serializado, que pode
  vir de terceiros. Aqui o prompt é o do desafio, então o risco é conhecido.

- O retorno é um ChatPromptTemplate. Para extrair o conteúdo das mensagens,
  use a serialização nativa do LangChain (`prompt.messages`, e o atributo
  `.prompt.template` de cada mensagem).

- Use `save_yaml` de utils.py para gravar o resultado no arquivo .yml.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from utils import save_yaml, check_env_vars, print_section_header

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")
PROMPT_NAME = "leonanluppi/bug_to_user_story_v1"
OUTPUT_PATH = PROJECT_ROOT / "prompts" / "bug_to_user_story_v1.yml"


def _message_text(message) -> str:
    """Extrai o template de uma mensagem LangChain serializada."""
    prompt_template = getattr(message, "prompt", None)
    template = getattr(prompt_template, "template", None)
    if template is not None:
        return str(template)

    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            str(block.get("text", block)) if isinstance(block, dict) else str(block)
            for block in content
        )
    return str(content)


def _message_role(message) -> str:
    role = getattr(message, "type", None) or getattr(message, "role", None)
    label = f"{role or ''} {message.__class__.__name__}".lower()
    if "system" in label:
        return "system_prompt"
    if "human" in label or "user" in label:
        return "user_prompt"
    return ""


def prompt_to_yaml_data(prompt) -> dict:
    """Converte um ChatPromptTemplate recebido do Hub para o formato local."""
    system_prompt = ""
    user_prompt = "{bug_report}"
    for message in getattr(prompt, "messages", []):
        role = _message_role(message)
        text = _message_text(message)
        if role == "system_prompt":
            system_prompt = text
        elif role == "user_prompt":
            user_prompt = text

    if not system_prompt and not user_prompt.strip():
        raise ValueError("O prompt retornado pelo LangSmith não contém mensagens reconhecíveis.")

    return {
        "bug_to_user_story_v1": {
            "description": "Prompt semente baixado do LangSmith Prompt Hub",
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "version": "v1",
            "tags": ["bug-analysis", "user-story", "product-management"],
        }
    }


def pull_prompts_from_langsmith() -> bool:
    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return False

    print(f"Puxando prompt: {PROMPT_NAME}")
    client = Client()
    prompt = client.pull_prompt(
        PROMPT_NAME,
        dangerously_pull_public_prompt=True,
    )
    data = prompt_to_yaml_data(prompt)
    if not save_yaml(data, str(OUTPUT_PATH)):
        return False

    print(f"Prompt salvo em: {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")
    return True


def main():
    """Função principal"""
    print_section_header("PULL DO PROMPT SEMENTE")
    try:
        return 0 if pull_prompts_from_langsmith() else 1
    except Exception as error:
        print(f"Falha ao baixar o prompt do LangSmith: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
