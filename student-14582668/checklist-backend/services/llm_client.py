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
