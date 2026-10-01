# MCP routes for the Attractions feature.
# Frontend calls these, backend forwards to the shared MCP server.

import traceback
import os
import json

from flask import Blueprint, jsonify, request

from services.mcp_client import (
    check_mcp_health,
    get_attractions_mcp,
    get_attractions_by_city_mcp,
    search_attractions_mcp,
    get_attraction_details_mcp,
    get_top_rated_attractions_mcp,
    call_mcp_tool,
)


mcp_bp = Blueprint("mcp", __name__)


# Only these tools can be called through /mcp/call.
# Keeps this feature from calling tools it doesn't own.
ALLOWED_MCP_TOOLS = {
    # Attractions tools
    "get_attractions",
    "get_attractions_by_city",
    "search_attractions",
    "get_attraction_details",
    "get_top_rated_attractions",

    # Shared tools
    "list_tripagent_services",
    "get_service_status",
    "list_available_tools",
    "get_tripagent_help",
    "get_system_summary",
}


# Checks the MCP_ENABLED env var (set to "false" in CI) and an
# optional per-request header, so MCP can be turned off for testing.
def mcp_mode_is_enabled() -> bool:
    enabled = os.getenv(
        "MCP_ENABLED",
        "true"
    ).strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )

    if not enabled:
        return False

    mode_header = request.headers.get(
        "X-MCP-Mode",
        "on"
    ).strip().lower()

    return mode_header in (
        "1",
        "true",
        "yes",
        "on",
    )


# GET /api/attractions/mcp/health - is the MCP server up?
@mcp_bp.route(
    "/api/attractions/mcp/health",
    methods=["GET"]
)
def mcp_health():

    try:

        check_mcp_health()

        return jsonify({
            "status": "connected"
        }), 200

    except Exception:

        return jsonify({
            "status": "error",
            "error":
                "MCP server unavailable."
        }), 503


# GET /api/attractions/mcp/all - call the get_attractions MCP tool.
@mcp_bp.route(
    "/api/attractions/mcp/all",
    methods=["GET"]
)
def get_all_attractions_mcp():

    try:
        result = get_attractions_mcp()

        return jsonify({
            "status": "success",
            "result": result
        }), 200

    except Exception as error:

        return jsonify({
            "status": "error",
            "error": str(error)
        }), 503


# POST /api/attractions/mcp/by-city - call get_attractions_by_city.
@mcp_bp.route(
    "/api/attractions/mcp/by-city",
    methods=["POST"]
)
def get_attractions_by_city_route():

    data = request.get_json(
        silent=True
    ) or {}

    city = str(
        data.get("city", "")
    ).strip()

    if not city:
        return jsonify({
            "status": "error",
            "error": "City is required."
        }), 400

    try:
        result = (
            get_attractions_by_city_mcp(
                city
            )
        )

        return jsonify({
            "status": "success",
            "result": result
        }), 200

    except Exception as error:

        return jsonify({
            "status": "error",
            "error": str(error)
        }), 503


# POST /api/attractions/mcp/search - call search_attractions.
@mcp_bp.route(
    "/api/attractions/mcp/search",
    methods=["POST"],
)
def attractions_mcp_search():
    data = request.get_json(silent=True) or {}

    city = data.get("city")
    category = data.get("category")
    max_price = data.get("max_price")

    try:
        result = search_attractions_mcp(
            city=city,
            category=category,
            max_price=max_price,
        )

        return jsonify({
            "status": "success",
            "result": result,
        }), 200

    except Exception as exc:
        traceback.print_exc()

        return jsonify({
            "status": "error",
            "error": "MCP service unavailable.",
            "details": str(exc),
        }), 503


# POST /api/attractions/mcp/details - call get_attraction_details.
@mcp_bp.route(
    "/api/attractions/mcp/details",
    methods=["POST"]
)
def attraction_details_mcp_route():

    data = request.get_json(
        silent=True
    ) or {}

    attraction_id = data.get(
        "attraction_id"
    )

    if attraction_id in ("", None):
        return jsonify({
            "status": "error",
            "error":
                "attraction_id is required."
        }), 400

    try:
        result = (
            get_attraction_details_mcp(
                attraction_id=attraction_id,
            )
        )

        return jsonify({
            "status": "success",
            "result": result
        }), 200

    except Exception as error:

        return jsonify({
            "status": "error",
            "error": str(error)
        }), 503


# POST /api/attractions/mcp/top-rated - call get_top_rated_attractions.
# This is the one the frontend demo button uses.
@mcp_bp.route(
    "/api/attractions/mcp/top-rated",
    methods=["POST"]
)
def top_rated_mcp_route():

    data = request.get_json(
        silent=True
    ) or {}

    city = data.get("city")
    limit = data.get("limit", 5)

    try:
        result = (
            get_top_rated_attractions_mcp(
                city=city,
                limit=limit,
            )
        )

        return jsonify({
            "status": "success",
            "result": result
        }), 200

    except Exception as error:

        return jsonify({
            "status": "error",
            "error": str(error)
        }), 503


# POST /api/attractions/mcp/call - generic: call any allowed tool by name.
# Blocked if MCP_ENABLED=false or the tool isn't in ALLOWED_MCP_TOOLS.
@mcp_bp.route(
    "/api/attractions/mcp/call",
    methods=["POST"]
)
def call_tool():

    if not mcp_mode_is_enabled():
        return jsonify({
            "status": "error",
            "error": "MCP Mode is disabled."
        }), 403

    data = request.get_json(
        silent=True
    ) or {}

    tool_name = str(
        data.get("tool", "")
    ).strip()

    arguments = data.get(
        "arguments",
        {}
    )

    if not tool_name:
        return jsonify({
            "status": "error",
            "error": "Tool name is required."
        }), 400

    if tool_name not in ALLOWED_MCP_TOOLS:
        return jsonify({
            "status": "error",
            "error":
                "Tool is not available "
                "to the Attractions feature."
        }), 403

    if not isinstance(arguments, dict):
        return jsonify({
            "status": "error",
            "error":
                "Arguments must be a JSON object."
        }), 400

    try:

        result = call_mcp_tool(
            tool_name,
            arguments,
        )

        parsed_result = result

        content = result.get("content", [])

        if content:
            try:
                parsed_content = [
                    json.loads(item)
                    for item in content
                ]

                if len(parsed_content) == 1:
                    parsed_result = parsed_content[0]
                else:
                    parsed_result = parsed_content

            except (
                json.JSONDecodeError,
                TypeError,
            ):
                parsed_result = result

        return jsonify({
            "status": "success",
            "tool": tool_name,
            "result": parsed_result,
        }), 200

    except Exception as error:

        return jsonify({
            "status": "error",
            "tool": tool_name,
            "error": str(error),
        }), 503
