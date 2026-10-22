"""Tests for the Flight Multi-Agent integration.

The shared Multi-Agent Server is stubbed so these tests verify the flight
backend's mode gating, evidence construction and human-review validation
without the non-containerised server running.
"""
from unittest.mock import Mock

import pytest

from app import app
from routes import multi_agent_routes


BASE = "/api/flight/multi-agent"

SAMPLE_FLIGHT = {
    "flight_id": 2,
    "airline": "Jetstar",
    "origin": "SYD",
    "destination": "MEL",
    "departure_time": "2026-09-15T11:20:00",
    "price": 109.0,
    "seat_availability": 64,
    "image": "jetstar-a320.jpg",
}


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_mode(monkeypatch):
    monkeypatch.delenv("MULTI_AGENT_LOCKED", raising=False)
    multi_agent_routes.set_mode_enabled(False)
    yield
    multi_agent_routes.set_mode_enabled(False)


@pytest.fixture
def evidence(monkeypatch):
    response = Mock()
    response.json = Mock(return_value=[SAMPLE_FLIGHT])
    response.raise_for_status = Mock()
    monkeypatch.setattr(
        multi_agent_routes, "list_flights", Mock(return_value=response)
    )


def test_mode_is_off_by_default(client):
    body = client.get(f"{BASE}/mode").get_json()

    assert body["enabled"] is False
    assert body["locked"] is False


def test_workflow_rejected_while_mode_is_off(client):
    response = client.post(
        f"{BASE}/workflow", json={"user_request": "Cheapest SYD to MEL"}
    )

    assert response.status_code == 403
    assert response.get_json()["error"] == "Multi-Agent mode is OFF"


def test_mode_can_be_enabled(client):
    response = client.put(f"{BASE}/mode", json={"enabled": True})

    assert response.status_code == 200
    assert response.get_json()["enabled"] is True


def test_mode_rejects_non_boolean(client):
    response = client.put(f"{BASE}/mode", json={"enabled": "yes"})

    assert response.status_code == 400


def test_mode_cannot_be_enabled_when_locked(client, monkeypatch):
    monkeypatch.setenv("MULTI_AGENT_LOCKED", "true")

    response = client.put(f"{BASE}/mode", json={"enabled": True})

    assert response.status_code == 403


def test_workflow_sends_flight_evidence_to_the_server(
    client, monkeypatch, evidence
):
    call = Mock(return_value={"workflow_id": "wf-1", "status": "queued"})
    monkeypatch.setattr(multi_agent_routes, "call_server", call)
    multi_agent_routes.set_mode_enabled(True)

    response = client.post(f"{BASE}/workflow", json={
        "user_request": "Cheapest flight to Melbourne",
        "origin": "syd",
        "destination": "mel",
    })

    assert response.status_code == 202
    assert response.get_json()["workflow_id"] == "wf-1"

    payload = call.call_args.kwargs["payload"]
    assert payload["feature"] == "flight"
    assert payload["context"]["constraints"]["evidence_only"] is True

    record = payload["context"]["evidence"][0]
    assert record["flight_id"] == 2
    assert "image" not in record


def test_workflow_rejects_empty_request(client, monkeypatch, evidence):
    multi_agent_routes.set_mode_enabled(True)

    response = client.post(f"{BASE}/workflow", json={"user_request": "   "})

    assert response.status_code == 400


def test_workflow_rejected_when_no_evidence_exists(client, monkeypatch):
    response = Mock()
    response.json = Mock(return_value=[])
    response.raise_for_status = Mock()
    monkeypatch.setattr(
        multi_agent_routes, "list_flights", Mock(return_value=response)
    )
    multi_agent_routes.set_mode_enabled(True)

    result = client.post(f"{BASE}/workflow", json={
        "user_request": "Flight from AAA to BBB",
        "origin": "AAA",
        "destination": "BBB",
    })

    assert result.status_code == 400


def test_human_review_accepts_valid_decision(client, monkeypatch):
    call = Mock(return_value={"workflow_id": "wf-1", "status": "reviewed"})
    monkeypatch.setattr(multi_agent_routes, "call_server", call)
    multi_agent_routes.set_mode_enabled(True)

    response = client.post(f"{BASE}/workflow/wf-1/review", json={
        "decision": "Partially Accept", "correction": "Prefer morning flights"
    })

    assert response.status_code == 200
    assert call.call_args.kwargs["payload"]["decision"] == "Partially Accept"


def test_human_review_rejects_unknown_decision(client, monkeypatch):
    multi_agent_routes.set_mode_enabled(True)

    response = client.post(
        f"{BASE}/workflow/wf-1/review", json={"decision": "Maybe"}
    )

    assert response.status_code == 400


def test_partial_accept_requires_a_correction(client, monkeypatch):
    multi_agent_routes.set_mode_enabled(True)

    response = client.post(f"{BASE}/workflow/wf-1/review", json={
        "decision": "Partially Accept", "correction": "   "
    })

    assert response.status_code == 400
