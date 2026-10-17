from unittest.mock import Mock

import pytest

from app import app
from routes import mcp_routes
from services import mcp_client


BASE = "/api/checklist-items/mcp"

EXPECTED_TOOLS = {
    "get_checklist_items",
    "get_checklist_item",
    "get_checklist_summary",
}


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def dependencies(monkeypatch):
    # Simulate enabled mode without contacting the real MCP server.
    monkeypatch.setattr(mcp_client, "MCP_ENABLED", True)

    tools = Mock(return_value=[
        {"name": name}
        for name in sorted(EXPECTED_TOOLS)
    ])

    call = Mock(return_value={"success": True})

    monkeypatch.setattr(mcp_routes, "list_tools", tools)
    monkeypatch.setattr(mcp_routes, "call_tool", call)

    return tools, call


def test_status_available(client):
    response = client.get(f"{BASE}/status")

    assert response.status_code == 200
    assert response.json["available"] is True
    assert response.json["missing_tools"] == []


def test_missing_tool_is_reported(client, dependencies):
    tools, _ = dependencies
    tools.return_value = [{"name": "get_checklist_items"}]

    response = client.get(f"{BASE}/status")

    assert response.status_code == 503
    assert response.json["available"] is False
    assert set(response.json["missing_tools"]) == {
        "get_checklist_item",
        "get_checklist_summary",
    }


def test_tools_are_filtered(client, dependencies):
    tools, _ = dependencies
    tools.return_value.append({"name": "unrelated_tool"})

    response = client.get(f"{BASE}/tools")

    assert response.status_code == 200
    assert response.json["count"] == 3
    assert {item["name"] for item in response.json["tools"]} == (
        EXPECTED_TOOLS
    )


@pytest.mark.parametrize(
    "name, arguments, result",
    [
        (
            "get_checklist_items",
            {"priority": "High", "is_completed": False},
            {"success": True, "count": 0, "items": []},
        ),
        (
            "get_checklist_item",
            {"item_id": 1},
            {"success": True, "item": {"item_id": 1}},
        ),
        (
            "get_checklist_summary",
            {},
            {"success": True, "summary": {"total": 0}},
        ),
    ],
)
def test_valid_call(client, dependencies, name, arguments, result):
    _, call = dependencies
    call.return_value = result

    response = client.post(
        f"{BASE}/call",
        json={"tool": name, "arguments": arguments},
    )

    assert response.status_code == 200
    assert response.json["result"] == result
    call.assert_called_once_with(name, arguments)


@pytest.mark.parametrize(
    "payload, status",
    [
        ([], 400),
        ({}, 400),
        ({"tool": "unrelated_tool"}, 403),
        ({"tool": "get_checklist_items", "arguments": []}, 400),
        (
            {"tool": "get_checklist_summary", "arguments": {"extra": 1}},
            400,
        ),
        ({"tool": "get_checklist_item", "arguments": {}}, 400),
        (
            {"tool": "get_checklist_item", "arguments": {"item_id": 0}},
            400,
        ),
        (
            {"tool": "get_checklist_item", "arguments": {"item_id": True}},
            400,
        ),
        (
            {"tool": "get_checklist_item", "arguments": {"item_id": "1"}},
            400,
        ),
        (
            {"tool": "get_checklist_items", "arguments": {"priority": "Urgent"}},
            400,
        ),
        (
            {"tool": "get_checklist_items", "arguments": {"item_type": "other"}},
            400,
        ),
        (
            {"tool": "get_checklist_items", "arguments": {"category": " "}},
            400,
        ),
        (
            {"tool": "get_checklist_items", "arguments": {"is_completed": "false"}},
            400,
        ),
    ],
)
def test_invalid_call_is_blocked(client, dependencies, payload, status):
    _, call = dependencies

    response = client.post(f"{BASE}/call", json=payload)

    assert response.status_code == status
    assert response.json["success"] is False
    call.assert_not_called()


def test_disabled_mode(client, dependencies, monkeypatch):
    monkeypatch.setattr(mcp_client, "MCP_ENABLED", False)
    tools, call = dependencies

    status = client.get(f"{BASE}/status")
    listing = client.get(f"{BASE}/tools")
    result = client.post(
        f"{BASE}/call",
        json={"tool": "get_checklist_summary"},
    )

    assert status.status_code == 200
    assert status.json["enabled"] is False
    assert status.json["available"] is False
    assert listing.status_code == 200
    assert listing.json["tools"] == []
    assert result.status_code == 403

    tools.assert_not_called()
    call.assert_not_called()


def test_connection_failure(client, dependencies):
    tools, call = dependencies
    tools.side_effect = mcp_client.MCPClientError("Unavailable")
    call.side_effect = mcp_client.MCPClientError("Unavailable")

    assert client.get(f"{BASE}/status").status_code == 503
    assert client.get(f"{BASE}/tools").status_code == 503

    response = client.post(
        f"{BASE}/call",
        json={"tool": "get_checklist_summary"},
    )

    assert response.status_code == 503
    assert response.json["success"] is False


def test_tool_failure(client, dependencies):
    _, call = dependencies
    call.return_value = {
        "success": False,
        "error": "Checklist item not found",
    }

    response = client.post(
        f"{BASE}/call",
        json={
            "tool": "get_checklist_item",
            "arguments": {"item_id": 999999},
        },
    )

    assert response.status_code == 502
    assert response.json["error"] == "Checklist item not found"