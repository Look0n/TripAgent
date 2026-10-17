import asyncio
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from collectors import mcp_collector as collector
from core.validation import finish


def result(value, error=False):
    return SimpleNamespace(structuredContent=value, content=[], isError=error)


class Session:
    def __init__(self, invalid=None, missing=False):
        self.calls = []
        self.invalid = invalid or {"success": False, "error": "item_id must be positive"}
        self.missing = missing

    async def list_tools(self):
        names = ["get_checklist_items", "get_checklist_item", "get_checklist_summary"]
        return SimpleNamespace(tools=[SimpleNamespace(name=n, inputSchema={"type": "object", "required": ["item_id"]}) for n in names if not (self.missing and n == "get_checklist_summary")])

    async def call_tool(self, name, args):
        self.calls.append((name, args))
        item = {"item_id": 42, "priority": "High", "is_completed": 0}
        if name == "get_checklist_items":
            return result({"success": True, "items": [item], "count": 1})
        if name == "get_checklist_summary":
            return result({"success": True, "summary": {"total": 1, "completed": 0, "pending": 1, "high_priority_pending": 1}})
        return result(self.invalid if args["item_id"] == 0 else {"success": True, "item": item})


def run(session):
    evidence = {"checks": [], "calls": []}
    asyncio.run(collector.run_cases(session, "checklist", evidence))
    return evidence


def test_dynamic_id_and_summary():
    session = Session()
    evidence = run(session)
    assert ("get_checklist_item", {"item_id": 42}) in session.calls
    assert all(row["status"] == "PASS" for row in evidence["checks"])


def test_upstream_failure_is_not_valid_input_rejection():
    evidence = run(Session(invalid={"success": False, "error": "Backend unavailable"}))
    assert evidence["checks"][-1]["status"] == "FAIL"


def test_missing_registered_tool_fails():
    evidence = run(Session(missing=True))
    assert evidence["checks"][0]["status"] == "FAIL"


def test_malformed_result():
    with pytest.raises(ValueError):
        collector.normalise(result([]))


def test_disabled_backend_is_not_boundary_success(monkeypatch):
    monkeypatch.setattr(collector.requests, "post", Mock(return_value=SimpleNamespace(status_code=403, json=lambda: {"error": "MCP tool mode is disabled"})))
    evidence = {"checks": []}
    collector.boundary_check("checklist", {"endpoints": {"base_url": "http://localhost:5004"}}, evidence)
    assert evidence["checks"][0]["status"] == "FAIL"


def test_account_boundary_is_unverified(monkeypatch):
    monkeypatch.delenv("LOOP_ACCOUNT_CUSTOMER_ID", raising=False)
    evidence = {"checks": []}
    collector.boundary_check("account", {}, evidence)
    assert finish(evidence, 0)[1]["validation_status"] == "PARTIAL"
