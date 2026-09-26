import os
import requests


RAG_SERVER_URL = os.getenv(
    "RAG_SERVER_URL",
    "http://host.docker.internal:7002",
)


def ask_rag(
    question: str,
    k: int = 5,
) -> dict:
    question = str(question or "").strip()

    if not question:
        raise ValueError("Question is required.")

    response = requests.post(
        f"{RAG_SERVER_URL}/rag/answer",
        json={
            "feature": "accommodation",
            "query": question,
            "k": k,
            "caller": "accommodation-backend",
        },
        timeout=120,
    )

    response.raise_for_status()

    return response.json()