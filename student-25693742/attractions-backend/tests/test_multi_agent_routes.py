"""Release 2 tests for the Attractions Multi-Agent routes.

The Multi-Agent Server and the attractions database are stubbed, so these
tests check mode control, the deployment lock, evidence building, validation
and human-review handling in the Attractions backend.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock

import pytest
import requests

from app import app as flask_app
from routes import multi_agent_routes
from services.multi_agent_client import MultiAgentClientError


BASE = "/api/attractions/multi-agent"

RECORDS = [
    {
        "attraction_id": 4,
        "name": "Sydney Opera House Tour",
        "category": "Culture",
        "city": "Sydney",
        "price": 49.0,
        "average_rating": 4.8,
        "image_url": "https://example.test/opera.jpg",
    },
]


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("MULTI_AGENT_LOCKED", raising=False)
    multi_agent_routes._state["enabled"] = False
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client

    multi_agent_routes._state["enabled"] = False


def enable(client):
    response = client.put(f"{BASE}/mode", json={"enabled": True})
    assert response.status_code == 200


def test_mode_is_off_by_default(client):
    response = client.get(f"{BASE}/mode")

    assert response.status_code == 200
    assert response.get_json() == {"enabled": False, "locked": False}


def test_workflow_refused_when_mode_off(client):
    response = client.post(f"{BASE}/workflow", json={"user_request": "museum"})

    assert response.status_code == 403
    assert response.get_json()["error"] == "Multi-Agent Mode is disabled."


def test_lock_prevents_enabling(client, monkeypatch):
    monkeypatch.setenv("MULTI_AGENT_LOCKED", "true")

    response = client.put(f"{BASE}/mode", json={"enabled": True})

    assert response.status_code == 403
    assert client.get(f"{BASE}/mode").get_json() == {
        "enabled": False,
        "locked": True,
    }


def test_mode_requires_boolean(client):
    response = client.put(f"{BASE}/mode", json={"enabled": "yes"})

    assert response.status_code == 400


def test_workflow_sends_database_evidence(client, monkeypatch):
    enable(client)
    db_stub = Mock(return_value=RECORDS)
    server_stub = Mock(return_value={"workflow_id": "wf-1", "status": "queued"})
    monkeypatch.setattr(multi_agent_routes, "get_all_attractions", db_stub)
    monkeypatch.setattr(multi_agent_routes, "call_server", server_stub)

    response = client.post(f"{BASE}/workflow", json={
        "user_request": "A culture tour in Sydney under $60",
        "city": "Sydney",
        "max_price": "60",
    })

    assert response.status_code == 202
    db_stub.assert_called_once_with(city="Sydney", category=None, max_price=60.0)

    method, path = server_stub.call_args.args
    payload = server_stub.call_args.kwargs["payload"]
    assert (method, path) == ("POST", "/workflow")
    assert payload["feature"] == "attractions"
    assert payload["context"]["constraints"]["evidence_only"] is True
    evidence = payload["context"]["evidence"]
    assert evidence[0]["attraction_id"] == 4
    assert "image_url" not in evidence[0]


def test_workflow_requires_request_text(client):
    enable(client)

    response = client.post(f"{BASE}/workflow", json={"user_request": "  "})

    assert response.status_code == 400


def test_workflow_rejects_bad_max_price(client):
    enable(client)

    response = client.post(f"{BASE}/workflow", json={
        "user_request": "anything",
        "max_price": "cheap",
    })

    assert response.status_code == 400


def test_workflow_without_evidence_is_rejected(client, monkeypatch):
    enable(client)
    monkeypatch.setattr(multi_agent_routes, "get_all_attractions", Mock(return_value=[]))

    response = client.post(f"{BASE}/workflow", json={
        "user_request": "A tour in Atlantis",
        "city": "Atlantis",
    })

    assert response.status_code == 400


def test_workflow_database_down_returns_503(client, monkeypatch):
    enable(client)
    monkeypatch.setattr(
        multi_agent_routes,
        "get_all_attractions",
        Mock(side_effect=requests.RequestException("down")),
    )

    response = client.post(f"{BASE}/workflow", json={"user_request": "museum"})

    assert response.status_code == 503


def test_server_unavailable_returns_controlled_error(client, monkeypatch):
    enable(client)
    monkeypatch.setattr(multi_agent_routes, "get_all_attractions", Mock(return_value=RECORDS))
    monkeypatch.setattr(
        multi_agent_routes,
        "call_server",
        Mock(side_effect=MultiAgentClientError("Multi-Agent Server unavailable.")),
    )

    response = client.post(f"{BASE}/workflow", json={"user_request": "museum"})

    assert response.status_code == 503
    assert response.get_json()["error"] == "Multi-Agent Server unavailable."


@pytest.mark.parametrize("decision", ["Approve", "", None])
def test_review_rejects_unknown_decision(client, decision):
    enable(client)

    response = client.post(f"{BASE}/workflow/wf-1/review", json={"decision": decision})

    assert response.status_code == 400


def test_partial_accept_requires_correction(client):
    enable(client)

    response = client.post(f"{BASE}/workflow/wf-1/review", json={
        "decision": "Partially Accept",
        "correction": " ",
    })

    assert response.status_code == 400


def test_review_forwards_human_decision(client, monkeypatch):
    enable(client)
    stub = Mock(return_value={"workflow_id": "wf-1", "status": "completed"})
    monkeypatch.setattr(multi_agent_routes, "call_server", stub)

    response = client.post(f"{BASE}/workflow/wf-1/review", json={
        "decision": "Partially Accept",
        "correction": "Only recommend the Opera House tour.",
    })

    assert response.status_code == 200
    payload = stub.call_args.kwargs["payload"]
    assert payload == {
        "feature": "attractions",
        "decision": "Partially Accept",
        "correction": "Only recommend the Opera House tour.",
    }


def test_modes_endpoint_reports_ci_baseline(client, monkeypatch):
    monkeypatch.setenv("AI_MODE_ENABLED", "false")
    monkeypatch.setenv("MCP_ENABLED", "false")
    monkeypatch.setenv("RAG_ENABLED", "false")
    monkeypatch.setenv("MULTI_AGENT_LOCKED", "true")

    response = client.get("/api/attractions/modes")

    assert response.get_json() == {
        "ai_mode": False,
        "mcp": False,
        "rag": False,
        "multi_agent": False,
        "multi_agent_locked": True,
    }


def test_disabled_services_refuse_calls(client, monkeypatch):
    monkeypatch.setenv("AI_MODE_ENABLED", "false")
    monkeypatch.setenv("MCP_ENABLED", "false")
    monkeypatch.setenv("RAG_ENABLED", "false")

    assert client.post("/api/attractions/recommend", json={"message": "x"}).status_code == 403
    assert client.post("/api/attractions/mcp/top-rated", json={}).status_code == 403
    assert client.post("/api/attractions/rag", json={"question": "x"}).status_code == 403
