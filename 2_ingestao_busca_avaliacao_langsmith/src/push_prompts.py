"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

DICAS DE IMPLEMENTAÇÃO:

- O push é feito pelo cliente do LangSmith:

      from langsmith import Client
      from langchain_core.prompts import ChatPromptTemplate

      client = Client()
      prompt = ChatPromptTemplate.from_messages([
          ("system", system_prompt),
          ("user", user_prompt),
      ])
      url = client.push_prompt(
          f"{username}/bug_to_user_story_v2",
          object=prompt,
          is_public=True,
          description="...",
          tags=[...],
      )

- `username` vem de USERNAME_LANGSMITH_HUB no .env e precisa ser o seu handle
  do Hub. Se você ainda não tem um handle, veja as instruções no .env.example.

- A variável do template precisa ser {bug_report}, que é a chave de entrada
  usada no dataset de avaliação.

- Use `load_yaml` de utils.py para ler o arquivo .yml.
"""

import sys
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")
PROMPT_PATH = PROJECT_ROOT / "prompts" / "bug_to_user_story_v2.yml"


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
    if not username:
        print("USERNAME_LANGSMITH_HUB não está configurada no .env.")
        return False

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("Prompt inválido:")
        for error in errors:
            print(f"  - {error}")
        return False

    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", prompt_data["system_prompt"]),
            ("human", prompt_data.get("user_prompt", "{bug_report}")),
        ]
    )
    techniques = prompt_data.get("techniques_applied", [])
    tags = list(prompt_data.get("tags", []))
    tags.extend(
        f"technique:{re.sub(r'[^a-z0-9-]+', '-', technique.lower()).strip('-')}"
        for technique in techniques
    )
    tags.append("version:v2")
    description = prompt_data.get(
        "description", "Prompt otimizado para transformar bugs em user stories."
    )
    prompt_id = f"{username}/{prompt_name}"

    try:
        client = Client()
        url = client.push_prompt(
            prompt_id,
            object=prompt_template,
            is_public=True,
            description=description,
            tags=tags,
        )
        print(f"Prompt publicado: {prompt_id}")
        print(f"URL: {url}")
        return True
    except Exception as error:
        print(f"Falha ao publicar {prompt_id}: {error}")
        return False


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []
    if not isinstance(prompt_data, dict):
        return False, ["O YAML deve conter um objeto de prompt."]

    is_valid, structure_errors = validate_prompt_structure(prompt_data)
    errors.extend(structure_errors)
    user_prompt = prompt_data.get("user_prompt", "")
    if "{bug_report}" not in user_prompt:
        errors.append("user_prompt deve conter a variável {bug_report}.")
    techniques = prompt_data.get("techniques_applied", [])
    if not isinstance(techniques, list) or len(techniques) < 2:
        errors.append("Liste pelo menos duas técnicas em techniques_applied.")
    return is_valid and not errors, errors


def main():
    """Função principal"""
    print_section_header("PUSH DO PROMPT OTIMIZADO")
    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    data = load_yaml(str(PROMPT_PATH))
    if not data:
        return 1
    prompt_data = data.get("bug_to_user_story_v2")
    if not prompt_data:
        print("A chave 'bug_to_user_story_v2' não foi encontrada no YAML.")
        return 1

    return 0 if push_prompt_to_langsmith("bug_to_user_story_v2", prompt_data) else 1


if __name__ == "__main__":
    sys.exit(main())
