from flask import Blueprint, jsonify, request

from services.mcp_client import (
    MCPClientError,
    call_tool,
    is_mcp_enabled,
    list_tools,
)


mcp_bp = Blueprint("checklist_mcp", __name__)


ALLOWED_TOOL_ARGUMENTS = {
    "get_checklist_items": {
        "item_type",
        "category",
        "priority",
        "is_completed",
    },
    "get_checklist_item": {
        "item_id",
    },
    "get_checklist_summary": set(),
}


@mcp_bp.get("/api/checklist-items/mcp/status")
def mcp_status():
    if not is_mcp_enabled():
        return jsonify({
            "enabled": False,
            "available": False,
            "message": "MCP mode is disabled",
        }), 200

    try:
        tools = list_tools()

    except MCPClientError as exc:
        return jsonify({
            "enabled": True,
            "available": False,
            "error": str(exc),
        }), 503

    names = {tool["name"] for tool in tools}
    missing = sorted(set(ALLOWED_TOOL_ARGUMENTS) - names)

    return jsonify({
        "enabled": True,
        "available": not missing,
        "missing_tools": missing,
    }), 200 if not missing else 503


@mcp_bp.get("/api/checklist-items/mcp/tools")
def mcp_tools():
    if not is_mcp_enabled():
        return jsonify({
            "enabled": False,
            "count": 0,
            "tools": [],
        }), 200

    try:
        tools = list_tools()

    except MCPClientError as exc:
        return jsonify({
            "success": False,
            "error": str(exc),
        }), 503

    allowed_tools = [
        tool
        for tool in tools
        if tool["name"] in ALLOWED_TOOL_ARGUMENTS
    ]

    return jsonify({
        "success": True,
        "count": len(allowed_tools),
        "tools": allowed_tools,
    }), 200


@mcp_bp.post("/api/checklist-items/mcp/call")
def mcp_call():
    if not is_mcp_enabled():
        return jsonify({
            "success": False,
            "error": "MCP mode is disabled",
        }), 403

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": "A JSON object is required",
        }), 400

    tool_name = data.get("tool")
    arguments = data.get("arguments", {})

    if not isinstance(tool_name, str) or not tool_name.strip():
        return jsonify({
            "success": False,
            "error": "Tool name is required",
        }), 400

    tool_name = tool_name.strip()

    if tool_name not in ALLOWED_TOOL_ARGUMENTS:
        return jsonify({
            "success": False,
            "error": "Tool is not available to the Checklist feature",
        }), 403

    if not isinstance(arguments, dict):
        return jsonify({
            "success": False,
            "error": "arguments must be a JSON object",
        }), 400

    unknown = set(arguments) - ALLOWED_TOOL_ARGUMENTS[tool_name]

    if unknown:
        return jsonify({
            "success": False,
            "error": "Unsupported tool arguments",
            "fields": sorted(unknown),
        }), 400

    if tool_name == "get_checklist_item":
        item_id = arguments.get("item_id")

        if type(item_id) is not int or item_id < 1:
            return jsonify({
                "success": False,
                "error": "A positive integer item_id is required",
            }), 400

    if tool_name == "get_checklist_items":
        item_type = arguments.get("item_type")
        priority = arguments.get("priority")
        category = arguments.get("category")
        is_completed = arguments.get("is_completed")

        if item_type is not None and item_type not in ("task", "packing"):
            return jsonify({
                "success": False,
                "error": "item_type must be task or packing",
            }), 400

        if priority is not None and priority not in ("High", "Medium", "Low"):
            return jsonify({
                "success": False,
                "error": "priority must be High, Medium, or Low",
            }), 400

        if category is not None and (
            not isinstance(category, str) or not category.strip()
        ):
            return jsonify({
                "success": False,
                "error": "category must be non-empty text",
            }), 400

        if is_completed is not None and not isinstance(is_completed, bool):
            return jsonify({
                "success": False,
                "error": "is_completed must be true or false",
            }), 400

    try:
        result = call_tool(tool_name, arguments)

    except MCPClientError as exc:
        return jsonify({
            "success": False,
            "error": str(exc),
        }), 503

    if result["success"] is False:
        return jsonify({
            "success": False,
            "tool": tool_name,
            "error": result.get("error", "MCP tool failed"),
        }), 502

    return jsonify({
        "success": True,
        "tool": tool_name,
        "result": result,
    }), 200