from pathlib import Path
from typing import Dict

from config import BASE_DIR


PROMPT_DIR = BASE_DIR / "prompt_templates"


def load_prompt(name: str) -> str:
    prompt_path = PROMPT_DIR / name
    return prompt_path.read_text(encoding="utf-8")


def render_prompt(name: str, variables: Dict[str, str]) -> str:
    template = load_prompt(name)
    return template.format(**variables)
