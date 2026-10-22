from unittest.mock import Mock

import pytest

from app import app
from routes import multi_agent_routes
from services import checklist_context, multi_agent_client


BASE = "/api/checklist-items/multi-agent"
WORKFLOW_ID = "bdea8522-da18-408a-9bce-1641e7cdbf67"


@pytest.fixture
def dependencies(monkeypatch):
    monkeypatch.setenv("MULTI_AGENT_ENABLED", "true")
    monkeypatch.setenv("MULTI_AGENT_LOCKED", "false")
    remote = Mock(side_effect=AssertionError("Unexpected external request"))
    monkeypatch.setattr(multi_agent_client.requests, "request", remote)
    response = Mock()
    response.json.return_value = [
        {"item_id": 1, "title": "Passport", "priority": "High", "is_completed": 0},
        {"item_id": 2, "title": "Tickets", "priority": "High", "is_completed": 1},
    ]
    database = Mock(return_value=response)
    monkeypatch.setattr(checklist_context.database_api, "get_checklist_items", database)
    return remote, database


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_start_uses_database_evidence(client, dependencies):
    remote, database = dependencies
    remote.side_effect = None
    remote.return_value.json.return_value = {
        "workflow_id": WORKFLOW_ID, "feature": "checklist", "status": "queued"
    }
    response = client.post(f"{BASE}/workflow", json={"user_request": " Review my trip "})
    assert response.status_code == 202
    database.assert_called_once_with()
    payload = remote.call_args.kwargs["json"]
    assert payload["user_request"] == "Review my trip"
    assert payload["context"]["summary"] == {
        "total": 2, "completed": 1, "pending": 1, "high_priority_pending": 1
    }
    assert payload["context"]["constraints"]["read_only"] is True


@pytest.mark.parametrize("setting", ["disabled", "locked"])
def test_disabled_or_locked_blocks_workflow(client, dependencies, monkeypatch, setting):
    if setting == "disabled":
        monkeypatch.setenv("MULTI_AGENT_ENABLED", "false")
    else:
        monkeypatch.setenv("MULTI_AGENT_LOCKED", "true")
    assert client.get(f"{BASE}/status").json == {"enabled": False, "available": False}
    assert client.post(f"{BASE}/workflow", json={"user_request": "Review"}).status_code == 403
    dependencies[0].assert_not_called()
    dependencies[1].assert_not_called()


@pytest.mark.parametrize("decision,status", [
    ("Accept", "completed"), ("Partially Accept", "completed"), ("Reject", "rejected")
])
def test_decision_is_forwarded_without_database_changes(client, dependencies, decision, status):
    remote, database = dependencies
    remote.side_effect = None
    remote.return_value.json.return_value = {
        "workflow_id": WORKFLOW_ID, "feature": "checklist", "status": status
    }
    response = client.post(f"{BASE}/workflow/{WORKFLOW_ID}/review", json={
        "decision": decision, "correction": "Prioritise passport"
    })
    assert response.status_code == 200
    assert response.json["status"] == status
    assert remote.call_args.kwargs["json"]["feature"] == "checklist"
    assert remote.call_args.kwargs["json"]["decision"] == decision
    database.assert_not_called()


def test_partial_accept_requires_correction(client, dependencies):
    response = client.post(f"{BASE}/workflow/{WORKFLOW_ID}/review", json={
        "decision": "Partially Accept", "correction": " "
    })
    assert response.status_code == 400
    dependencies[0].assert_not_called()


@pytest.mark.parametrize("feature,status", [("flight", 200), ("checklist", 409)])
def test_wrong_feature_and_repeat_review_errors(client, dependencies, feature, status):
    remote, _ = dependencies
    remote.side_effect = None
    remote.return_value.ok = status == 200
    remote.return_value.status_code = status
    remote.return_value.json.return_value = {
        "workflow_id": WORKFLOW_ID, "feature": feature, "status": "completed",
        "error": "Workflow already reviewed"
    }
    response = client.post(f"{BASE}/workflow/{WORKFLOW_ID}/review", json={"decision": "Accept"})
    assert response.status_code == (502 if feature == "flight" else 409)


def test_timeout_returns_gateway_timeout(client, dependencies):
    dependencies[0].side_effect = multi_agent_client.requests.Timeout()
    assert client.get(f"{BASE}/workflow/{WORKFLOW_ID}").status_code == 504
