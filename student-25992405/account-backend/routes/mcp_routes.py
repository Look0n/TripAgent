from flask import Blueprint, jsonify, request

from routes.normal_ui import login_required
from services.mcp_client import (
    MCPClientError,
    call_tool,
    check_mcp_status,
    is_mcp_enabled,
    list_tools,
    set_mcp_enabled,
)


mcp_bp = Blueprint(
    "mcp",
    __name__
)


ACCOUNT_TOOLS = {
    "get_customer_profile",
    "get_customer_preferences",
    "update_customer_preferences",
    "get_customer_summary",
    "check_profile_completeness",
}

SHARED_TOOLS = {
    "list_tripagent_services",
    "get_service_status",
    "list_available_tools",
    "get_tripagent_help",
    "get_system_summary",
}

ALLOWED_TOOLS = ACCOUNT_TOOLS | SHARED_TOOLS

CUSTOMER_TOOLS = {
    "get_customer_profile",
    "get_customer_preferences",
    "update_customer_preferences",
    "get_customer_summary",
    "check_profile_completeness",
}


@mcp_bp.route(
    "/api/account/mcp/mode",
    methods=["GET", "PUT"]
)
def mcp_mode():
    customer_id, error = login_required()

    if error:
        return error

    if request.method == "GET":
        return jsonify({
            "enabled": is_mcp_enabled()
        }), 200

    data = request.get_json(silent=True) or {}
    enabled = data.get("enabled")

    if not isinstance(enabled, bool):
        return jsonify({
            "error": "enabled must be true or false"
        }), 400

    current_mode = set_mcp_enabled(enabled)

    return jsonify({
        "enabled": current_mode,
        "message": (
            "MCP mode enabled."
            if current_mode
            else "MCP mode disabled."
        )
    }), 200


@mcp_bp.route(
    "/api/account/mcp/status",
    methods=["GET"]
)
def mcp_status():
    customer_id, error = login_required()

    if error:
        return error

    status = check_mcp_status()

    # Disabled is an intentional mode, not a server failure.
    if not status.get("enabled", True):
        return jsonify(status), 200

    code = 200 if status["available"] else 503
    return jsonify(status), code


@mcp_bp.route(
    "/api/account/mcp/tools",
    methods=["GET"]
)
def mcp_tools():
    customer_id, error = login_required()

    if error:
        return error

    if not is_mcp_enabled():
        return jsonify({
            "feature": "account",
            "enabled": False,
            "count": 0,
            "tools": [],
            "message": "MCP mode is disabled."
        }), 200

    try:
        server_tools = list_tools()
    except MCPClientError as exc:
        return jsonify({
            "error": str(exc)
        }), 503

    tools = [
        tool
        for tool in server_tools
        if tool.get("name") in ALLOWED_TOOLS
    ]

    return jsonify({
        "feature": "account",
        "count": len(tools),
        "tools": tools,
    }), 200


@mcp_bp.route(
    "/api/account/mcp/call",
    methods=["POST"]
)
def mcp_call():
    customer_id, error = login_required()

    if error:
        return error

    if not is_mcp_enabled():
        return jsonify({
            "error": "MCP mode is disabled."
        }), 409

    data = request.get_json(silent=True) or {}
    tool_name = str(data.get("tool", "")).strip()
    arguments = data.get("arguments") or {}

    if not tool_name:
        return jsonify({
            "error": "Tool name is required"
        }), 400

    if tool_name not in ALLOWED_TOOLS:
        return jsonify({
            "error": "This MCP tool is not available to the Account feature"
        }), 403

    if not isinstance(arguments, dict):
        return jsonify({
            "error": "Tool arguments must be a JSON object"
        }), 400

    # Never trust customer identity supplied by the browser.
    # Account-specific tools always receive the authenticated ID
    # forwarded by the shared gateway.
    arguments.pop("customer_id", None)

    if tool_name in CUSTOMER_TOOLS:
        arguments["customer_id"] = customer_id

    # Account callers may only ask for their own tool view.
    if tool_name == "list_available_tools":
        arguments["feature"] = "account"

    try:
        result = call_tool(
            tool_name,
            arguments,
        )
    except MCPClientError as exc:
        return jsonify({
            "error": str(exc)
        }), 503

    return jsonify({
        "tool": tool_name,
        "result": result,
    }), 200
