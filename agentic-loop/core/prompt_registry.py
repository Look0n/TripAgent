from pathlib import Path
import re


PROMPTS_ROOT = Path(__file__).resolve().parents[2] / "prompts" / "service"


def load_prompt(prompt_name):
    name = prompt_name if prompt_name.endswith(".txt") else f"{prompt_name}.txt"
    path = (PROMPTS_ROOT / name).resolve()
    if not path.is_relative_to(PROMPTS_ROOT.resolve()):
        raise ValueError("Prompt path must stay inside prompts/service.")
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Empty prompt file: {path}")
    return text


def render_prompt(template, values):
    placeholder_pattern = r"\{\{([A-Z_]+)\}\}"
    remaining = re.sub(placeholder_pattern, "", template)
    if "{{" in remaining or "}}" in remaining:
        raise ValueError("Invalid placeholder in prompt template.")

    def replace(match):
        key = match.group(1)
        if key not in values:
            raise ValueError(f"Missing prompt value: {key}")
        return str(values[key])

    return re.sub(placeholder_pattern, replace, template)
