import os
import requests

RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://host.docker.internal:7002").rstrip("/")
RAG_FEATURE = "account"
_rag_enabled = os.getenv("RAG_ENABLED", "true").lower() == "true"

class RAGClientError(Exception):
    pass

def is_rag_enabled():
    return _rag_enabled

def set_rag_enabled(enabled):
    global _rag_enabled
    _rag_enabled = bool(enabled)
    return _rag_enabled

def _post(path, payload):
    if not _rag_enabled:
        raise RAGClientError("RAG mode is disabled.")
    body = dict(payload)
    body["feature"] = RAG_FEATURE
    body["caller"] = "account-backend"
    try:
        response = requests.post(f"{RAG_SERVICE_URL}{path}", json=body, timeout=120)
        data = response.json()
        if not response.ok:
            raise RAGClientError(data.get("error", f"RAG service returned HTTP {response.status_code}"))
        return data
    except RAGClientError:
        raise
    except (requests.RequestException, ValueError) as exc:
        raise RAGClientError(f"Unable to contact shared RAG service: {exc}") from exc

def check_rag_status():
    if not _rag_enabled:
        return {"enabled": False, "available": False, "message": "RAG mode is disabled."}
    try:
        response = requests.get(f"{RAG_SERVICE_URL}/health", timeout=5)
        response.raise_for_status()
        return {"enabled": True, "available": True, "service_url": RAG_SERVICE_URL}
    except requests.RequestException as exc:
        return {"enabled": True, "available": False, "service_url": RAG_SERVICE_URL, "error": str(exc)}

def retrieve_context(query, k=5):
    return _post("/rag/retrieve", {"query": query, "k": k})

def answer_question(query, k=5):
    return _post("/rag/answer", {"query": query, "k": k})

def refresh_account_corpus():
    return _post("/rag/refresh", {})
