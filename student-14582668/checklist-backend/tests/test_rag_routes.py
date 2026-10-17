from unittest.mock import Mock

import pytest

from app import app
from routes import rag_routes
from services import rag_client


BASE = "/api/checklist-items/rag"


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def dependencies(monkeypatch):
    monkeypatch.setattr(rag_client, "RAG_ENABLED", True)

    health_response = Mock()
    health_response.raise_for_status.return_value = None
    health_response.json.return_value = {"status": "healthy"}

    health = Mock(return_value=health_response)
    monkeypatch.setattr(rag_client.requests, "get", health)

    # Fail immediately if a test accidentally sends a real POST.
    post = Mock(side_effect=AssertionError("Unexpected external POST"))
    monkeypatch.setattr(rag_client.requests, "post", post)

    operations = {
        "refresh": Mock(return_value={
            "status": "success",
            "feature": "checklist",
            "chunk_count": 17,
            "vector_store_status": "ready",
        }),
        "retrieve": Mock(return_value={
            "status": "success",
            "feature": "checklist",
            "results": [],
        }),
        "answer": Mock(return_value={
            "status": "success",
            "feature": "checklist",
            "answer": "AI suggestions are not saved automatically.",
            "citations": [{
                "chunk_id": "checklist_knowledge_ai_suggestions",
                "source_id": "rag-knowledge:checklist",
                "authority_tier": "tier_2",
            }],
            "confidence_category": "Low",
        }),
    }

    monkeypatch.setattr(
        rag_routes, "refresh_checklist_corpus", operations["refresh"]
    )
    monkeypatch.setattr(
        rag_routes, "retrieve_context", operations["retrieve"]
    )
    monkeypatch.setattr(
        rag_routes, "answer_question", operations["answer"]
    )

    return operations, health, post


def test_status_available(client):
    response = client.get(f"{BASE}/status")

    assert response.status_code == 200
    assert response.json["enabled"] is True
    assert response.json["available"] is True


def test_refresh(client, dependencies):
    operations, _, _ = dependencies

    response = client.post(f"{BASE}/refresh")

    assert response.status_code == 200
    assert response.json == operations["refresh"].return_value
    operations["refresh"].assert_called_once_with()


@pytest.mark.parametrize("endpoint", ["retrieve", "answer"])
@pytest.mark.parametrize("k", [1, 20])
def test_valid_question(client, dependencies, endpoint, k):
    operations, _, _ = dependencies

    response = client.post(
        f"{BASE}/{endpoint}",
        json={"query": "  Checklist priorities  ", "k": k},
    )

    assert response.status_code == 200
    assert response.json == operations[endpoint].return_value
    operations[endpoint].assert_called_once_with(
        "Checklist priorities", k
    )


def test_default_k(client, dependencies):
    operations, _, _ = dependencies

    response = client.post(
        f"{BASE}/answer",
        json={"query": "Checklist priorities"},
    )

    assert response.status_code == 200
    operations["answer"].assert_called_once_with(
        "Checklist priorities", 5
    )


@pytest.mark.parametrize("endpoint", ["retrieve", "answer"])
@pytest.mark.parametrize(
    "payload",
    [
        [],
        {},
        {"query": ""},
        {"query": "   "},
        {"query": 123},
        {"query": "x" * 2001},
        {"query": "Checklist", "k": 0},
        {"query": "Checklist", "k": 21},
        {"query": "Checklist", "k": True},
        {"query": "Checklist", "k": "5"},
        {"query": "Checklist", "k": 1.5},
        {"query": "Checklist", "feature": "account"},
    ],
)
def test_invalid_question(client, dependencies, endpoint, payload):
    operations, _, _ = dependencies

    response = client.post(f"{BASE}/{endpoint}", json=payload)

    assert response.status_code == 400
    assert response.json["status"] == "error"
    operations[endpoint].assert_not_called()


def test_disabled_mode(client, dependencies, monkeypatch):
    monkeypatch.setattr(rag_client, "RAG_ENABLED", False)
    operations, health, post = dependencies

    status = client.get(f"{BASE}/status")

    assert status.status_code == 200
    assert status.json["enabled"] is False
    assert status.json["available"] is False

    for endpoint in ("refresh", "retrieve", "answer"):
        response = client.post(
            f"{BASE}/{endpoint}",
            json={"query": "Checklist"},
        )
        assert response.status_code == 403
        operations[endpoint].assert_not_called()

    health.assert_not_called()
    post.assert_not_called()


@pytest.mark.parametrize("endpoint", ["refresh", "retrieve", "answer"])
@pytest.mark.parametrize("status_code", [502, 503, 504])
def test_service_error(client, dependencies, endpoint, status_code):
    operations, _, _ = dependencies

    operations[endpoint].side_effect = rag_client.RAGClientError(
        "RAG request failed",
        status_code,
    )

    response = client.post(
        f"{BASE}/{endpoint}",
        json={"query": "Checklist"},
    )

    assert response.status_code == status_code
    assert response.json["status"] == "error"
    assert response.json["error"] == "RAG request failed"


def test_status_unavailable(client, dependencies):
    _, health, _ = dependencies
    health.side_effect = rag_client.requests.ConnectionError(
        "Connection refused"
    )

    response = client.get(f"{BASE}/status")

    assert response.status_code == 503
    assert response.json["enabled"] is True
    assert response.json["available"] is False