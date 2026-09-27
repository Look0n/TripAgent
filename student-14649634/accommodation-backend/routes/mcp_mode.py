import traceback

from flask import Blueprint, jsonify, request

from services.mcp_client import (
    get_accommodations_mcp,
    get_accommodation_by_city_mcp,
    search_accommodations_mcp,
    check_accommodation_availability_mcp,
)


mcp_bp = Blueprint("mcp", __name__)


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