from flask import Blueprint, jsonify, request

from services.database_api import (
    get_all_accommodations,
    get_accommodation_by_id,
    create_accommodation,
    update_accommodation,
    delete_accommodation
)


normal_bp = Blueprint(
    "normal_ui",
    __name__
)


@normal_bp.route(
    "/api/accommodations",
    methods=["GET"]
)
def get_accommodations():

    city = request.args.get("city")
    accommodation_type = request.args.get("type")
    max_price = request.args.get("max_price")

    if max_price:
        try:
            max_price = float(max_price)

        except ValueError:
            return jsonify({
                "error": "max_price must be a number"
            }), 400


    accommodations = get_all_accommodations(
        city,
        accommodation_type,
        max_price
    )


    return jsonify(accommodations)


@normal_bp.route(
    "/api/accommodations/<int:accommodation_id>",
    methods=["GET"]
)
def get_accommodation(accommodation_id):

    accommodation = get_accommodation_by_id(
        accommodation_id
    )


    if accommodation is None:
        return jsonify({
            "error": "Accommodation not found"
        }), 404


    return jsonify(accommodation)


@normal_bp.route(
    "/api/accommodations",
    methods=["POST"]
)
def create():

    data = request.get_json()


    required_fields = [
        "accommodation_name",
        "type",
        "city",
        "price_per_night",
        "guest_capacity"
    ]


    for field in required_fields:

        if field not in data:

            return jsonify({
                "error": f"Missing required field: {field}"
            }), 400


    accommodation = create_accommodation(
        data
    )


    return jsonify(
        accommodation
    ), 201


@normal_bp.route(
    "/api/accommodations/<int:accommodation_id>",
    methods=["PUT"]
)
def update(accommodation_id):

    data = request.get_json()


    accommodation = update_accommodation(
        accommodation_id,
        data
    )


    if accommodation is None:

        return jsonify({
            "error": "Accommodation not found"
        }), 404


    return jsonify(
        accommodation
    )


@normal_bp.route(
    "/api/accommodations/<int:accommodation_id>",
    methods=["DELETE"]
)
def delete(accommodation_id):

    success = delete_accommodation(
        accommodation_id
    )


    if not success:

        return jsonify({
            "error": "Accommodation not found"
        }), 404


    return jsonify({
        "message":
            "Accommodation deleted successfully"
    })