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

import os
import sys
from datetime import date
from pathlib import Path
import yaml
from dotenv import load_dotenv
from langsmith import Client
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()


def _str_representer(dumper, value):
    """Grava strings multilinha no estilo bloco (|) para o YAML ficar legível."""
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


# save_yaml usa yaml.dump com o Dumper padrão, então o representer vale para ele
yaml.add_representer(str, _str_representer)

SOURCE_PROMPT = "leonanluppi/bug_to_user_story_v1"
PROMPT_KEY = "bug_to_user_story_v1"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "prompts" / f"{PROMPT_KEY}.yml"

# Mapeia a classe da mensagem do LangChain para o campo correspondente no YAML
MESSAGE_FIELDS = {
    "SystemMessagePromptTemplate": "system_prompt",
    "HumanMessagePromptTemplate": "user_prompt",
    "AIMessagePromptTemplate": "ai_prompt",
}


def extract_prompt_data(prompt) -> dict:
    """
    Converte o ChatPromptTemplate retornado pelo Hub no formato YAML do projeto.

    Args:
        prompt: ChatPromptTemplate retornado por client.pull_prompt

    Returns:
        Dicionário com description, system_prompt, user_prompt e metadados
    """
    data = {"description": "Prompt para converter relatos de bugs em User Stories"}

    for message in prompt.messages:
        field = MESSAGE_FIELDS.get(type(message).__name__)
        template = getattr(getattr(message, "prompt", None), "template", None)
        if field and template is not None:
            data[field] = template

    metadata = getattr(prompt, "metadata", None) or {}
    data["version"] = "v1"
    data["source"] = SOURCE_PROMPT
    data["pulled_at"] = date.today().isoformat()
    data["input_variables"] = list(prompt.input_variables)
    data["tags"] = metadata.get("lc_hub_tags") or ["bug-analysis", "user-story", "product-management"]

    return data


def pull_prompts_from_langsmith():
    """
    Faz pull do prompt semente do LangSmith Hub e salva em prompts/bug_to_user_story_v1.yml.

    Returns:
        True se sucesso, False caso contrário
    """
    client = Client()

    print(f"Puxando prompt: {SOURCE_PROMPT}")
    try:
        prompt = client.pull_prompt(SOURCE_PROMPT, dangerously_pull_public_prompt=True)
    except Exception as e:
        print(f"Erro ao fazer pull do prompt '{SOURCE_PROMPT}': {e}")
        return False

    print(f"   Prompt carregado ({len(prompt.messages)} mensagens)")

    prompt_data = extract_prompt_data(prompt)
    if not prompt_data.get("system_prompt"):
        print("Aviso: o prompt não contém mensagem de sistema")

    if not save_yaml({PROMPT_KEY: prompt_data}, str(OUTPUT_PATH)):
        return False

    print(f"   Salvo em prompts/{OUTPUT_PATH.name}")
    return True


def main():
    """Função principal"""
    print_section_header("PULL DE PROMPTS DO LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    if not pull_prompts_from_langsmith():
        return 1

    print("\nPull concluído com sucesso!")
    print("\nPróximo passo: otimize o prompt em prompts/bug_to_user_story_v2.yml")
    return 0


if __name__ == "__main__":
    sys.exit(main())
