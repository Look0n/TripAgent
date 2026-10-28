from unittest.mock import Mock

import pytest

from app import app
from services import mcp_client, rag_client, multi_agent_client, llm_client


@pytest.fixture(params=["mcp", "rag"])
def mode(request, monkeypatch):
    name = request.param
    service = mcp_client if name == "mcp" else rag_client
    monkeypatch.setattr(service, f"{name.upper()}_ENABLED", False)
    monkeypatch.setenv(f"{name.upper()}_LOCKED", "false")
    return name, service


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_all_modes_start_off():
    assert llm_client.AI_MODE_ENABLED is False
    assert mcp_client.MCP_ENABLED is False
    assert rag_client.RAG_ENABLED is False
    assert multi_agent_client.MULTI_AGENT_ENABLED is False


def test_switch_off_on_off_without_contacting_shared_servers(client, mode, monkeypatch):
    name, _ = mode
    external = Mock(side_effect=AssertionError("Mode changes must not contact shared services"))
    monkeypatch.setattr(mcp_client, "_list_tools_async", external)
    monkeypatch.setattr(rag_client.requests, "get", external)
    base = f"/api/checklist-items/{name}"
    other = rag_client.RAG_ENABLED if name == "mcp" else mcp_client.MCP_ENABLED
    agent = multi_agent_client.MULTI_AGENT_ENABLED

    for enabled in (False, True, False):
        response = client.post(f"{base}/mode", json={"enabled": enabled})
        assert response.status_code == 200
        assert response.json == {"enabled": enabled, "locked": False}
        assert client.get(f"{base}/mode").json == response.json

    assert client.get(f"{base}/status").json["available"] is False
    assert (rag_client.RAG_ENABLED if name == "mcp" else mcp_client.MCP_ENABLED) == other
    assert multi_agent_client.MULTI_AGENT_ENABLED == agent
    external.assert_not_called()


@pytest.mark.parametrize("payload", [{}, [], {"enabled": 1}, {"enabled": "true"}, {"enabled": None}])
def test_mode_requires_boolean(client, mode, payload):
    name, _ = mode
    base = f"/api/checklist-items/{name}"
    assert client.post(f"{base}/mode", json=payload).status_code == 400
    assert client.get(f"{base}/mode").json["enabled"] is False


def test_locked_mode_cannot_be_enabled(client, mode, monkeypatch):
    name, service = mode
    monkeypatch.setenv(f"{name.upper()}_LOCKED", "true")
    base = f"/api/checklist-items/{name}"
    assert client.post(f"{base}/mode", json={"enabled": True}).status_code == 403
    assert client.get(f"{base}/mode").json == {"enabled": False, "locked": True}
    monkeypatch.setattr(service, f"{name.upper()}_ENABLED", True)
    assert client.get(f"{base}/mode").json["enabled"] is False
    assert client.post(f"{base}/mode", json={"enabled": False}).status_code == 200


def test_off_blocks_operations(client, mode):
    name, _ = mode
    base = f"/api/checklist-items/{name}"
    client.post(f"{base}/mode", json={"enabled": True})
    client.post(f"{base}/mode", json={"enabled": False})
    operations = [("call", {"tool": "get_checklist_summary", "arguments": {}})] if name == "mcp" else [
        ("refresh", {}), ("retrieve", {"query": "Passport"}), ("answer", {"query": "Passport"}),
    ]
    for path, payload in operations:
        assert client.post(f"{base}/{path}", json=payload).status_code == 403


@pytest.mark.parametrize("locked", [False, True])
def test_ai_mode_switch_and_gate(client, monkeypatch, locked):
    monkeypatch.setattr(llm_client, "AI_MODE_ENABLED", False)
    monkeypatch.setenv("AI_MODE_LOCKED", str(locked))
    external = Mock(side_effect=AssertionError("Disabled AI must not call dependencies"))
    monkeypatch.setattr("routes.ai_mode.generate_text", external)
    monkeypatch.setattr("routes.ai_mode.database_api.get_checklist_items", external)
    base = "/api/checklist-items"
    assert client.get(f"{base}/ai/mode").json == {"enabled": False, "locked": locked}
    assert client.post(f"{base}/recommend", json={"message": "Travel checklist"}).status_code == 403
    response = client.post(f"{base}/ai/mode", json={"enabled": True})
    assert response.status_code == (403 if locked else 200)
    assert client.get(f"{base}/ai/mode").json["enabled"] is (not locked)
    if not locked:
        assert client.post(f"{base}/recommend", json={}).status_code == 400
    assert client.post(f"{base}/ai/mode", json={"enabled": False}).status_code == 200
    assert client.post(f"{base}/recommend", json={"message": "Travel checklist"}).status_code == 403
    if locked:
        monkeypatch.setattr(llm_client, "AI_MODE_ENABLED", True)
        assert client.post(f"{base}/recommend", json={"message": "Travel checklist"}).status_code == 403
    external.assert_not_called()


@pytest.mark.parametrize("payload", [{}, [], {"enabled": 1}, {"enabled": "true"}, {"enabled": None}])
def test_ai_mode_requires_boolean(client, monkeypatch, payload):
    monkeypatch.setattr(llm_client, "AI_MODE_ENABLED", False)
    assert client.post("/api/checklist-items/ai/mode", json=payload).status_code == 400
    assert client.get("/api/checklist-items/ai/mode").json["enabled"] is False
