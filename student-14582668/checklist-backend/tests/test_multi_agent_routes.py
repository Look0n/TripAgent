from unittest.mock import Mock

import pytest

from app import app
from services import checklist_context, multi_agent_client


BASE = "/api/checklist-items/multi-agent"
WORKFLOW_ID = "bdea8522-da18-408a-9bce-1641e7cdbf67"


@pytest.fixture
def dependencies(monkeypatch):
    monkeypatch.setattr(multi_agent_client, "MULTI_AGENT_ENABLED", True)
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
    for operation in ("create_checklist_item", "update_checklist_item", "delete_checklist_item"):
        monkeypatch.setattr(
            checklist_context.database_api,
            operation,
            Mock(side_effect=AssertionError("Review must not change checklist items")),
        )
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
    assert payload["feature"] == "checklist"
    assert payload["context"]["constraints"]["human_review_required"] is True
    assert [item["item_id"] for item in payload["context"]["evidence"]] == [1, 2]
    assert remote.call_args.kwargs["method"] == "POST"
    assert remote.call_args.kwargs["url"].endswith("/workflow")


@pytest.mark.parametrize("setting", ["disabled", "locked"])
def test_disabled_or_locked_blocks_workflow(client, dependencies, monkeypatch, setting):
    if setting == "disabled":
        monkeypatch.setattr(multi_agent_client, "MULTI_AGENT_ENABLED", False)
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
    assert remote.call_args.kwargs["json"]["correction"] == "Prioritise passport"
    assert remote.call_args.kwargs["url"].endswith(f"/workflow/{WORKFLOW_ID}/review")
    database.assert_not_called()


@pytest.mark.parametrize("payload", [
    [], {}, {"user_request": " "}, {"user_request": 123},
    {"user_request": "x" * 4001},
])
def test_start_rejects_invalid_request_before_collecting_evidence(client, dependencies, payload):
    response = client.post(f"{BASE}/workflow", json=payload)
    assert response.status_code == 400
    dependencies[0].assert_not_called()
    dependencies[1].assert_not_called()


def test_start_does_not_trust_client_feature_or_evidence(client, dependencies):
    remote, _ = dependencies
    remote.side_effect = None
    remote.return_value.json.return_value = {
        "workflow_id": WORKFLOW_ID, "feature": "checklist", "status": "queued"
    }
    response = client.post(f"{BASE}/workflow", json={
        "user_request": "Review", "feature": "flight",
        "context": {"evidence": [{"item_id": 999, "title": "Invented item"}]},
    })
    assert response.status_code == 202
    payload = remote.call_args.kwargs["json"]
    assert payload["feature"] == "checklist"
    assert [item["item_id"] for item in payload["context"]["evidence"]] == [1, 2]


def test_start_reports_database_failure_without_starting_workflow(client, dependencies):
    remote, database = dependencies
    database.side_effect = multi_agent_client.requests.ConnectionError()
    assert client.post(f"{BASE}/workflow", json={"user_request": "Review"}).status_code == 503
    remote.assert_not_called()


@pytest.mark.parametrize("items", [{"items": []}, ["invalid"], [{"item_id": "1"}]])
def test_start_rejects_malformed_database_evidence(client, dependencies, items):
    remote, database = dependencies
    database.return_value.json.return_value = items
    assert client.post(f"{BASE}/workflow", json={"user_request": "Review"}).status_code == 502
    remote.assert_not_called()


def test_start_rejects_oversized_evidence(client, dependencies):
    remote, database = dependencies
    database.return_value.json.return_value = [
        {"item_id": 1, "title": "x" * 12000, "is_completed": 0}
    ]
    assert client.post(f"{BASE}/workflow", json={"user_request": "Review"}).status_code == 413
    remote.assert_not_called()


@pytest.mark.parametrize("payload", [
    [], {}, {"decision": "Approve"}, {"decision": ["Accept"]},
    {"decision": "Accept", "correction": 1},
    {"decision": "Accept", "correction": "x" * 4001},
])
def test_review_rejects_invalid_input_without_server_call(client, dependencies, payload):
    response = client.post(f"{BASE}/workflow/{WORKFLOW_ID}/review", json=payload)
    assert response.status_code == 400
    dependencies[0].assert_not_called()
    dependencies[1].assert_not_called()


def test_review_rejects_response_for_another_workflow(client, dependencies):
    remote, _ = dependencies
    remote.side_effect = None
    remote.return_value.json.return_value = {
        "workflow_id": "6a48bf35-bcf5-452e-bd28-131bf090f645",
        "feature": "checklist", "status": "completed",
    }
    response = client.post(f"{BASE}/workflow/{WORKFLOW_ID}/review", json={"decision": "Accept"})
    assert response.status_code == 502


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


def test_mode_defaults_off(client, monkeypatch):
    monkeypatch.setenv("MULTI_AGENT_ENABLED", "true")
    monkeypatch.setenv("MULTI_AGENT_LOCKED", "false")
    assert client.get(f"{BASE}/mode").json == {"enabled": False, "locked": False}


def test_mode_can_be_switched_without_contacting_shared_server(client, dependencies):
    for enabled in (False, True, False):
        response = client.post(f"{BASE}/mode", json={"enabled": enabled})
        assert response.status_code == 200
        assert response.json == {"enabled": enabled, "locked": False}
        assert client.get(f"{BASE}/mode").json == response.json
    assert client.post(f"{BASE}/workflow", json={"user_request": "Review"}).status_code == 403
    assert client.get(f"{BASE}/workflow/{WORKFLOW_ID}").status_code == 403
    assert client.post(f"{BASE}/workflow/{WORKFLOW_ID}/review", json={"decision": "Accept"}).status_code == 403
    dependencies[0].assert_not_called()
    dependencies[1].assert_not_called()


def test_locked_mode_cannot_be_enabled(client, dependencies, monkeypatch):
    monkeypatch.setenv("MULTI_AGENT_LOCKED", "true")
    assert client.post(f"{BASE}/mode", json={"enabled": True}).status_code == 403
    assert client.get(f"{BASE}/mode").json == {"enabled": False, "locked": True}
    assert client.post(f"{BASE}/mode", json={"enabled": False}).status_code == 200
    dependencies[0].assert_not_called()


@pytest.mark.parametrize("payload", [{}, [], {"enabled": "true"}, {"enabled": 1}, {"enabled": None}])
def test_mode_rejects_invalid_input(client, dependencies, payload):
    assert client.post(f"{BASE}/mode", json=payload).status_code == 400
    assert client.get(f"{BASE}/mode").json["enabled"] is True
