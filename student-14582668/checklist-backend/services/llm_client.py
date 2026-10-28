import os

import requests


OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://127.0.0.1:11434/api/generate"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5:0.5b"
)


# Checklist starts OFF; the UI controls this backend process only.
AI_MODE_ENABLED = False


def is_ai_mode_enabled() -> bool:
    return AI_MODE_ENABLED and not is_ai_mode_locked()


def is_ai_mode_locked() -> bool:
    return os.getenv("AI_MODE_LOCKED", "false").strip().lower() in ("1", "true", "yes", "on")


def set_ai_mode_enabled(enabled: bool) -> None:
    global AI_MODE_ENABLED
    AI_MODE_ENABLED = enabled


def generate_text(
    prompt,
    timeout=120,
    json_format=True,
    num_predict=500,
    temperature=0.2
):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": num_predict,
            "temperature": temperature,
            "num_ctx": 2048
        }
    }

    if json_format:
        payload["format"] = "json"

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=timeout
    )

    response.raise_for_status()

    result = response.json()
    generated_text = result.get("response", "")

    if not isinstance(generated_text, str):
        raise ValueError("Ollama returned an invalid response")

    return generated_text.strip()
