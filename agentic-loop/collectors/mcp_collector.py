import ast
import asyncio
import json
import os
import time

import requests
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from config.review_config import MCP_SERVER_URL, MCP_TIMEOUT_SECONDS
from config.validation_cases import MCP_CASES
from core.validation import ROOT, check, finish, sanitise, structure


def normalise(result):
    value = result.structuredContent
    if value is None:
        texts = [block.text for block in result.content if getattr(block, "type", None) == "text"]
        if len(texts) != 1:
            raise ValueError("Expected one JSON tool result")
        value = json.loads(texts[0])
    if not isinstance(value, dict):
        raise ValueError("Expected a tool result object")
    return value


def successful(value):
    return value.get("success") is True or value.get("status") == "success"


async def run_cases(session, feature, evidence):
    case = MCP_CASES[feature]
    tools = {tool.name: tool for tool in (await session.list_tools()).tools}
    evidence["registered_tools"] = sorted(tools)
    check(evidence, "registered_tools", set(case["tools"]) <= tools.keys(), {"missing": sorted(set(case["tools"]) - tools.keys())})
    for name in case["tools"]:
        if name in tools:
            schema = tools[name].inputSchema
            check(evidence, f"schema:{name}", isinstance(schema, dict) and schema.get("type") == "object")
    if case["invalid_tool"] in tools:
        schema = tools[case["invalid_tool"]].inputSchema
        check(evidence, "required_argument_schema", set(case["invalid_arguments"]) <= set(schema.get("required", [])))
    async def call(name, arguments):
        started = time.monotonic()
        result = await asyncio.wait_for(session.call_tool(name, arguments), MCP_TIMEOUT_SECONDS)
        value = normalise(result)
        evidence["calls"].append({"tool": name, "arguments": sanitise(arguments), "is_error": result.isError, "response": sanitise(value), "duration_seconds": round(time.monotonic() - started, 3)})
        return result.isError, value
    arguments = dict(case["arguments"])
    account_id = os.getenv("LOOP_ACCOUNT_CUSTOMER_ID", "")
    if feature == "account" and not account_id:
        check(evidence, "normal_call", False, "Set LOOP_ACCOUNT_CUSTOMER_ID to an authorised test customer", "SKIP")
    else:
        if feature == "account":
            arguments["customer_id"] = int(account_id)
            if arguments["customer_id"] < 1:
                raise ValueError("LOOP_ACCOUNT_CUSTOMER_ID must be positive")
        error, data = await call(case["list_tool"], arguments)
        ok = not error and successful(data)
        rows = data.get(case.get("list_key")) if case.get("list_key") else None
        if case.get("list_key"):
            ok = ok and isinstance(rows, list) and all(isinstance(row, dict) for row in rows) and type(data.get("count")) is int and data["count"] == len(rows)
        else:
            ok = ok and isinstance(data.get(case["object_key"]), dict)
        check(evidence, "normal_call", ok)
        if case.get("single_tool"):
            if ok and rows:
                item_id = rows[0][case["id_field"]]
                error, single = await call(case["single_tool"], {case["id_field"]: item_id})
                item = single.get(case["object_key"])
                check(evidence, "single_call", not error and successful(single) and isinstance(item, dict) and item.get(case["id_field"]) == item_id)
            else:
                check(evidence, "single_call", False, "No valid source record available", "SKIP")
        if feature == "checklist":
            error, summary = await call("get_checklist_summary", {})
            expected = None
            if ok:
                completed = sum(row.get("is_completed") in (1, True) for row in rows)
                expected = {"total": len(rows), "completed": completed, "pending": len(rows) - completed, "high_priority_pending": sum(row.get("priority") == "High" and row.get("is_completed") in (0, False) for row in rows)}
            check(evidence, "summary_counts", expected is not None and not error and successful(summary) and summary.get("summary") == expected, {"expected": expected, "note": "Run against a stable test dataset"})
    error, invalid = await call(case["invalid_tool"], case["invalid_arguments"])
    message = str(invalid.get("error", "")).lower()
    rejected = error or invalid.get("success") is False or invalid.get("status") == "error"
    check(evidence, "invalid_arguments", rejected and all(term in message for term in case["error_terms"]), {"expected_terms": case["error_terms"]})


def boundary_check(feature, service, evidence):
    headers = {}
    foreign_tool = "get_customer_profile"
    arguments = {"customer_id": 0}
    if feature == "account":
        customer_id = os.getenv("LOOP_ACCOUNT_CUSTOMER_ID", "")
        if not customer_id:
            check(evidence, "backend_tool_boundary", False, "Set an authorised LOOP_ACCOUNT_CUSTOMER_ID; browser-session validation remains separate", "SKIP")
            return
        if int(customer_id) < 1:
            raise ValueError("Test customer ID must be positive")
        headers["X-Customer-ID"] = customer_id
        foreign_tool = "get_checklist_summary"
        arguments = {}
    prefix = {"account": "/api/account", "checklist": "/api/checklist-items", "accommodation": "/api/accommodations", "attractions": "/api/attractions", "flight": "/api/flight"}[feature]
    url = service["endpoints"]["base_url"] + prefix + "/mcp/call"
    response = requests.post(url, json={"tool": foreign_tool, "arguments": arguments}, headers=headers, timeout=10)
    data = response.json()
    error = str(data.get("error", "")).lower() if isinstance(data, dict) else ""
    check(evidence, "backend_tool_boundary", response.status_code == 403 and "tool" in error and "disabled" not in error and "off" not in error, {"url": url, "status": response.status_code, "response": sanitise(data)})


def collect_mcp_context(feature, service):
    started = time.monotonic()
    evidence = {"feature": feature, "server": MCP_SERVER_URL, "checks": [], "calls": [], "limitations": ["Read-only sample calls; write tools are registration-only", "Direct MCP is not an authenticated UI test", "Account backend boundary uses the existing trusted X-Customer-ID contract, not browser authentication"]}
    structure(evidence, ["shared/mcp-server/mcp_server.py", "shared/mcp-server/tool_registry.py", "shared/mcp-server/requirements.txt", f"{service['backend_dir']}/app.py", "prompts/service/implementation/tool_selection_prompt.txt", "prompts/service/review/integration_review_prompt.txt"])
    try:
        tree = ast.parse((ROOT / "shared/mcp-server/tool_registry.py").read_text(encoding="utf-8-sig"))
        name = feature.upper() + "_TOOLS"
        declared = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == name for target in node.targets))
        check(evidence, "registry_contract", set(declared) == set(MCP_CASES[feature]["tools"]), {"declared": declared, "expected": MCP_CASES[feature]["tools"]})
    except (OSError, ValueError, SyntaxError, StopIteration) as exc:
        check(evidence, "registry_contract", False, type(exc).__name__)
    async def execute():
        async with streamable_http_client(MCP_SERVER_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await asyncio.wait_for(session.initialize(), MCP_TIMEOUT_SECONDS)
                await run_cases(session, feature, evidence)
    try:
        asyncio.run(asyncio.wait_for(execute(), MCP_TIMEOUT_SECONDS * 8))
    except Exception as exc:
        check(evidence, "mcp_execution", False, {"error_type": type(exc).__name__, "message": "Connection, protocol or tool execution failed"})
    try:
        boundary_check(feature, service, evidence)
    except (requests.RequestException, ValueError) as exc:
        check(evidence, "backend_tool_boundary", False, type(exc).__name__)
    return finish(evidence, started)
