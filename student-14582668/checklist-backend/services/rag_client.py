import os
import requests

RAG_SERVICE_URL = os.getenv(
    "RAG_SERVICE_URL",
    "http://localhost:7002",
).rstrip("/")

RAG_ENABLED = os.getenv(
    "RAG_ENABLED",
    "true",
).strip().lower() in ("1", "true", "yes", "on")

RAG_TIMEOUT_SECONDS = 150


class RAGClientError(RuntimeError):
    def __init__(self, message: str, status_code: int = 503):
        super().__init__(message)
        self.status_code = status_code


def is_rag_enabled() -> bool:
    return RAG_ENABLED


def check_rag_status() -> dict:
    if not is_rag_enabled():
        return {
            "enabled": False,
            "available": False,
            "message": "RAG mode is disabled",
        }

    try:
        response = requests.get(
            f"{RAG_SERVICE_URL}/health",
            timeout=5,
        )
        response.raise_for_status()
        payload = response.json()

        if (
            not isinstance(payload, dict)
            or payload.get("status") != "healthy"
        ):
            raise RAGClientError(
                "Shared RAG service returned an invalid health response",
                502,
            )

    except requests.RequestException as exc:
        raise RAGClientError(
            "Shared RAG service is unavailable"
        ) from exc

    except ValueError as exc:
        raise RAGClientError(
            "Shared RAG service returned invalid JSON",
            502,
        ) from exc

    return {
        "enabled": True,
        "available": True,
        "message": "Shared RAG HTTP service is available",
    }


def _post(path: str, payload=None) -> dict:
    if not is_rag_enabled():
        raise RAGClientError("RAG mode is disabled", 403)

    body = dict(payload or {})
    body["feature"] = "checklist"
    body["caller"] = "checklist-backend"

    try:
        response = requests.post(
            f"{RAG_SERVICE_URL}{path}",
            json=body,
            timeout=(5, RAG_TIMEOUT_SECONDS),
        )

    except requests.Timeout as exc:
        raise RAGClientError(
            "Shared RAG request timed out",
            504,
        ) from exc

    except requests.RequestException as exc:
        raise RAGClientError(
            "Unable to connect to the shared RAG service"
        ) from exc

    try:
        result = response.json()

    except ValueError as exc:
        raise RAGClientError(
            "Shared RAG service returned invalid JSON",
            502,
        ) from exc

    if not isinstance(result, dict):
        raise RAGClientError(
            "Shared RAG service returned an invalid response",
            502,
        )

    if not response.ok or result.get("status") != "success":
        error = result.get("error")

        if not isinstance(error, str) or not error.strip():
            error = "Shared RAG service could not complete the request"

        raise RAGClientError(error, 502)

    if result.get("feature") != "checklist":
        raise RAGClientError(
            "Shared RAG service returned a different feature",
            502,
        )

    return result


def refresh_checklist_corpus() -> dict:
    return _post("/rag/refresh")


def retrieve_context(query: str, k: int = 5) -> dict:
    result = _post(
        "/rag/retrieve",
        {"query": query, "k": k},
    )

    results = result.get("results")

    if not isinstance(results, list) or not all(
        isinstance(item, dict) for item in results
    ):
        raise RAGClientError(
            "Shared RAG service returned invalid search results",
            502,
        )

    return result


def answer_question(query: str, k: int = 5) -> dict:
    result = _post(
        "/rag/answer",
        {"query": query, "k": k},
    )

    answer = result.get("answer")
    citations = result.get("citations")

    if (
        not isinstance(answer, str)
        or not answer.strip()
        or not isinstance(citations, list)
        or not all(isinstance(item, dict) for item in citations)
        or result.get("confidence_category")
        not in ("High", "Medium", "Low", "Unknown")
    ):
        raise RAGClientError(
            "Shared RAG service returned an invalid answer response",
            502,
        )

    return result