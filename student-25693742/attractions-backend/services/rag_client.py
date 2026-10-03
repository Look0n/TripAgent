# RAG client for the Attractions backend.
# Talks to the shared RAG server (also runs on the host, not in Docker).
# "feature": "attractions" tells the RAG server which corpus to search.

import os
import requests


RAG_SERVER_URL = os.getenv(
    "RAG_SERVICE_URL",
    "http://host.docker.internal:7002",
)


# Quick check that the RAG server is reachable.
def check_rag_health():
    response = requests.get(
        f"{RAG_SERVER_URL}/health",
        timeout=3,
    )

    response.raise_for_status()

    return response.json()


# Full grounded answer: retrieve context + generate answer + citations.
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
            "feature": "attractions",
            "query": question,
            "k": k,
            "caller": "attractions-backend",
        },
        timeout=120,
    )

    response.raise_for_status()

    return response.json()


# Retrieval only (no LLM answer) - useful to see raw matched chunks.
def retrieve_rag(
    question: str,
    k: int = 5,
) -> dict:

    response = requests.post(
        f"{RAG_SERVER_URL}/rag/retrieve",
        json={
            "feature": "attractions",
            "query": question,
            "k": k,
            "caller": "attractions-backend",
        },
        timeout=120,
    )

    response.raise_for_status()

    return response.json()


# Rebuild the attractions corpus + vector index on the RAG server.
def refresh_rag() -> dict:

    response = requests.post(
        f"{RAG_SERVER_URL}/rag/refresh",
        json={
            "feature": "attractions",
            "caller": "attractions-backend",
        },
        timeout=120,
    )

    response.raise_for_status()

    return response.json()
