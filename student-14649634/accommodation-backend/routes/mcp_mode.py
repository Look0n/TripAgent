import traceback

from flask import Blueprint, jsonify, request

from services.mcp_client import search_accommodations_mcp


mcp_bp = Blueprint("mcp", __name__)


@mcp_bp.route(
    "/api/accommodations/mcp/search",
    methods=["POST"],
)
def accommodation_mcp_search():
    data = request.get_json(silent=True) or {}

    city = data.get("city", "").strip()
    max_price = data.get("max_price")
    guests = data.get("guests")

    if not city:
        return jsonify({
            "error": "City is required."
        }), 400

    try:
        result = search_accommodations_mcp(
            city=city,
            max_price=max_price,
            guests=guests,
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