"""
Testes automatizados para validação de prompts.
"""
import re
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt():
    data = load_prompts(PROMPT_FILE)
    assert PROMPT_KEY in data, f"Chave '{PROMPT_KEY}' não encontrada em {PROMPT_FILE.name}"
    return data[PROMPT_KEY]


@pytest.fixture(scope="module")
def system_prompt(prompt):
    return prompt.get("system_prompt") or ""


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt
        assert isinstance(prompt["system_prompt"], str)
        assert prompt["system_prompt"].strip()

    def test_prompt_has_role_definition(self, system_prompt):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        assert re.search(r"Você é um[a]? ", system_prompt), "Persona não definida com 'Você é um...'"
        assert "Product Manager" in system_prompt

    def test_prompt_mentions_format(self, system_prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        lowered = system_prompt.lower()
        assert "markdown" in lowered or "formato padrão" in lowered
        assert "Como um" in system_prompt and "eu quero" in system_prompt and "para que" in system_prompt
        assert "Critérios de Aceitação" in system_prompt
        for keyword in ("Dado que", "Quando", "Então"):
            assert keyword in system_prompt

    def test_prompt_has_few_shot_examples(self, system_prompt):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        examples = re.findall(r"^#+\s*Exemplo \d+", system_prompt, flags=re.MULTILINE)
        inputs = re.findall(r"^Entrada:", system_prompt, flags=re.MULTILINE)
        outputs = re.findall(r"^Saída:", system_prompt, flags=re.MULTILINE)

        assert len(examples) >= 2, "São necessários pelo menos 2 exemplos few-shot"
        assert len(inputs) == len(outputs) == len(examples), "Cada exemplo precisa de Entrada e Saída"

    def test_prompt_no_todos(self, prompt):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        for field in ("system_prompt", "user_prompt", "description"):
            text = prompt.get(field) or ""
            assert "[TODO]" not in text, f"'[TODO]' encontrado em {field}"
            assert "TODO" not in text, f"'TODO' encontrado em {field}"

    def test_minimum_techniques(self, prompt):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt.get("techniques_applied", [])
        assert isinstance(techniques, list)
        assert len(techniques) >= 2
        assert any("few-shot" in t.lower() for t in techniques), "Few-shot é obrigatório"

    def test_user_prompt_has_bug_report_variable(self, prompt, system_prompt):
        """A variável {bug_report} deve estar só no user_prompt (no v1 ela era duplicada)."""
        assert "{bug_report}" in (prompt.get("user_prompt") or "")
        assert "{bug_report}" not in system_prompt

    def test_system_prompt_has_no_template_braces(self, system_prompt):
        """Chaves soltas no system_prompt seriam interpretadas como variáveis pelo ChatPromptTemplate."""
        assert not re.search(r"(?<!\{)\{[^{}]*\}(?!\})", system_prompt)

    def test_prompt_has_edge_cases(self, system_prompt):
        """O prompt deve orientar o tratamento de casos especiais."""
        assert "edge cases" in system_prompt.lower()

    def test_prompt_structure_is_valid(self, prompt):
        """Usa o validador de utils.py (campos obrigatórios, TODOs e técnicas)."""
        is_valid, errors = validate_prompt_structure(prompt)
        assert is_valid, errors


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
