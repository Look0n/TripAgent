import traceback
import os
import json

from flask import Blueprint, jsonify, request

from services.mcp_client import (
    check_mcp_health,
    get_accommodations_mcp,
    get_accommodation_by_city_mcp,
    search_accommodations_mcp,
    check_accommodation_availability_mcp,
    call_mcp_tool,
)


mcp_bp = Blueprint("mcp", __name__)


ALLOWED_MCP_TOOLS = {
    # Accommodation tools
    "get_accommodations",
    "get_accommodation_by_city",
    "search_accommodations",
    "check_accommodation_availability",

    # Shared tools
    "list_tripagent_services",
    "get_service_status",
    "list_available_tools",
    "get_tripagent_help",
    "get_system_summary",
}


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
    
    
@mcp_bp.route(
    "/api/accommodations/mcp/health",
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
            

@mcp_bp.route(
    "/api/accommodations/mcp/all",
    methods=["GET"]
)
def get_all_accommodations():

    try:
        result = get_accommodations_mcp()

        return jsonify({
            "status": "success",
            "result": result
        }), 200

    except Exception as error:

        return jsonify({
            "status": "error",
            "error": str(error)
        }), 503


@mcp_bp.route(
    "/api/accommodations/mcp/by-city",
    methods=["POST"]
)
def get_accommodations_by_city():

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
            get_accommodation_by_city_mcp(
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


@mcp_bp.route(
    "/api/accommodations/mcp/search",
    methods=["POST"],
)
def accommodation_mcp_search():
    data = request.get_json(silent=True) or {}

    city = data.get("city", "").strip()
    max_price = data.get("max_price")
    guests = data.get("guests")
    type = data.get("type")

    if not city:
        return jsonify({
            "error": "City is required."
        }), 400

    try:
        result = search_accommodations_mcp(
            city=city,
            max_price=max_price,
            guests=guests,
            type=type,
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
        
        
@mcp_bp.route(
    "/api/accommodations/mcp/availability",
    methods=["POST"]
)
def check_availability():

    data = request.get_json(
        silent=True
    ) or {}

    accommodation_id = data.get(
        "accommodation_id"
    )

    check_in = str(
        data.get("check_in", "")
    ).strip()

    check_out = str(
        data.get("check_out", "")
    ).strip()


    if accommodation_id in ("", None):
        return jsonify({
            "status": "error",
            "error":
                "Accommodation ID is required."
        }), 400

    if not check_in or not check_out:
        return jsonify({
            "status": "error",
            "error":
                "Check-in and check-out "
                "dates are required."
        }), 400


    try:
        result = (
            check_accommodation_availability_mcp(
                accommodation_id=
                    accommodation_id,
                check_in=check_in,
                check_out=check_out,
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
        
        
@mcp_bp.route(
    "/api/accommodations/mcp/call",
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
                "to the Accommodation feature."
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