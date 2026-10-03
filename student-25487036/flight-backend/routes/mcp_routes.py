from flask import Blueprint, jsonify, request

from services.mcp_client import (
    MCPClientError,
    call_tool,
    check_mcp_status,
    is_mcp_enabled,
    list_tools,
    set_mcp_enabled,
)
from views.html_formatters import (
    format_mcp_result,
    format_mcp_tool_list,
)


mcp_bp = Blueprint(
    "mcp",
    __name__
)


HTML_HEADERS = {"Content-Type": "text/html; charset=utf-8"}


FLIGHT_TOOLS = {
    "search_flights",
    "get_flight",
    "get_flights_by_route",
    "get_cheapest_flight",
    "check_seat_availability",
}

SHARED_TOOLS = {
    "list_tripagent_services",
    "get_service_status",
    "list_available_tools",
    "get_tripagent_help",
    "get_system_summary",
}

ALLOWED_TOOLS = FLIGHT_TOOLS | SHARED_TOOLS


@mcp_bp.route("/api/flight/mcp/mode", methods=["GET", "PUT"])
def mcp_mode():
    if request.method == "GET":
        return jsonify({"enabled": is_mcp_enabled()}), 200

    data = request.get_json(silent=True) or {}
    enabled = data.get("enabled")

    if not isinstance(enabled, bool):
        return jsonify({
            "error": "enabled must be true or false"
        }), 400

    return jsonify({"enabled": set_mcp_enabled(enabled)}), 200


@mcp_bp.route("/api/flight/mcp/status", methods=["GET"])
def mcp_status():
    return jsonify(check_mcp_status()), 200


@mcp_bp.route("/api/flight/mcp/tools", methods=["GET"])
def mcp_tools():
    try:
        tools = list_tools()
    except MCPClientError as exc:
        return jsonify({"error": str(exc)}), 503

    permitted = [
        tool for tool in tools
        if tool.get("name") in ALLOWED_TOOLS
    ]

    return jsonify({
        "feature": "flight",
        "allowed_tool_count": len(permitted),
        "server_tool_count": len(tools),
        "tools": permitted,
    }), 200


@mcp_bp.route("/api/flight/mcp/call", methods=["POST"])
def mcp_call():
    data = request.get_json(silent=True) or {}

    tool_name = str(data.get("tool") or "").strip()
    arguments = data.get("arguments") or {}

    if not tool_name:
        return jsonify({"error": "tool is required"}), 400

    if not isinstance(arguments, dict):
        return jsonify({
            "error": "arguments must be an object"
        }), 400

    if tool_name not in ALLOWED_TOOLS:
        return jsonify({
            "error": (
                f"The flight feature is not permitted to call "
                f"'{tool_name}'."
            ),
            "allowed_tools": sorted(ALLOWED_TOOLS),
        }), 403

    try:
        result = call_tool(tool_name, arguments)
    except MCPClientError as exc:
        return jsonify({"error": str(exc)}), 503

    return jsonify({
        "feature": "flight",
        "tool": tool_name,
        "arguments": arguments,
        "result": result,
    }), 200


@mcp_bp.route("/api/flight/mcp/tools/html", methods=["GET"])
def mcp_tools_html():
    try:
        tools = list_tools()
    except MCPClientError as exc:
        return (
            f'<p class="warning">MCP unavailable: {exc}</p>',
            503,
            HTML_HEADERS,
        )

    permitted = [
        tool for tool in tools
        if tool.get("name") in ALLOWED_TOOLS
    ]

    return format_mcp_tool_list(permitted), 200, HTML_HEADERS


@mcp_bp.route("/api/flight/mcp/call/html", methods=["POST"])
def mcp_call_html():
    tool_name = str(request.form.get("tool") or "").strip()

    if not tool_name:
        return (
            '<p class="warning">Select a tool to run.</p>',
            400,
            HTML_HEADERS,
        )

    if tool_name not in ALLOWED_TOOLS:
        return (
            f'<p class="warning">The flight feature is not permitted '
            f'to call {tool_name}.</p>',
            403,
            HTML_HEADERS,
        )

    arguments = {}

    origin = str(request.form.get("origin") or "").strip().upper()
    destination = str(
        request.form.get("destination") or ""
    ).strip().upper()
    flight_id = str(request.form.get("flight_id") or "").strip()
    max_price = str(request.form.get("max_price") or "").strip()

    if tool_name in {
        "search_flights",
        "get_flights_by_route",
        "get_cheapest_flight",
    }:
        if not origin:
            return (
                '<p class="warning">Origin is required for this tool.</p>',
                400,
                HTML_HEADERS,
            )

        arguments["origin"] = origin

        if destination:
            arguments["destination"] = destination

        if tool_name in {
            "get_flights_by_route",
            "get_cheapest_flight",
        } and not destination:
            return (
                '<p class="warning">Destination is required for '
                'this tool.</p>',
                400,
                HTML_HEADERS,
            )

        if tool_name == "search_flights" and max_price:
            try:
                arguments["max_price"] = float(max_price)
            except ValueError:
                return (
                    '<p class="warning">Max price must be a number.</p>',
                    400,
                    HTML_HEADERS,
                )

    if tool_name in {"get_flight", "check_seat_availability"}:
        if not flight_id.isdigit():
            return (
                '<p class="warning">A numeric flight ID is required '
                'for this tool.</p>',
                400,
                HTML_HEADERS,
            )

        arguments["flight_id"] = int(flight_id)

    try:
        result = call_tool(tool_name, arguments)
    except MCPClientError as exc:
        return (
            f'<p class="warning">MCP call failed: {exc}</p>',
            503,
            HTML_HEADERS,
        )

    return (
        format_mcp_result(tool_name, arguments, result),
        200,
        HTML_HEADERS,
    )
