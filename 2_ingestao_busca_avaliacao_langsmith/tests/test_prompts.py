"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
import re
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROJECT_ROOT = Path(__file__).parent.parent
PROMPT_PATH = PROJECT_ROOT / "prompts" / "bug_to_user_story_v2.yml"

def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

class TestPrompts:
    @classmethod
    def setup_class(cls):
        data = load_prompts(str(PROMPT_PATH))
        cls.prompt = data["bug_to_user_story_v2"]

    def test_prompt_has_system_prompt(self):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert self.prompt.get("system_prompt", "").strip()

    def test_prompt_has_role_definition(self):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        assert re.search(
            r"voc[eê] [ée] um product manager",
            self.prompt["system_prompt"],
            re.IGNORECASE,
        )

    def test_prompt_mentions_format(self):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        prompt_text = self.prompt["system_prompt"] + "\n" + self.prompt.get("user_prompt", "")
        assert "Como [persona]" in prompt_text
        assert "Critérios de Aceitação" in prompt_text

    def test_prompt_has_few_shot_examples(self):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        prompt_text = self.prompt["system_prompt"]
        assert "Exemplo 1" in prompt_text
        assert "Entrada:" in prompt_text
        assert "Saída:" in prompt_text

    def test_prompt_no_todos(self):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        assert "[TODO]" not in self.prompt["system_prompt"]
        assert "[TODO]" not in self.prompt.get("user_prompt", "")

    def test_minimum_techniques(self):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        assert len(self.prompt.get("techniques_applied", [])) >= 2

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
