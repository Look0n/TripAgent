import os
import requests


RAG_SERVER_URL = os.getenv(
    "RAG_SERVER_URL",
    "http://host.docker.internal:7002",
)


def check_rag_health():
    response = requests.get(
        f"{RAG_SERVER_URL}/health",
        timeout=3,
    )

    response.raise_for_status()

    return response.json()


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


def retrieve_rag(
    question: str,
    k: int = 5,
) -> dict:

    response = requests.post(
        f"{RAG_SERVER_URL}/rag/retrieve",
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


def refresh_rag() -> dict:

    response = requests.post(
        f"{RAG_SERVER_URL}/rag/refresh",
        json={
            "feature": "accommodation",
            "caller": "accommodation-backend",
        },
        timeout=120,
    )

    response.raise_for_status()

    return response.json()