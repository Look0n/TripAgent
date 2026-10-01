import os

from openai import OpenAI


OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://ollama:11434/v1"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5:0.5b"
)


client = OpenAI(
    base_url=OLLAMA_BASE_URL,
    api_key="ollama"
)


def generate_response(system_prompt, user_prompt):
    completion = client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
        timeout=60
    )

    return completion.choices[0].message.content.strip()

    