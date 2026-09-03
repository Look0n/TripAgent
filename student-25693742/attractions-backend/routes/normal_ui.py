from flask import Blueprint, jsonify, request
import requests

from services import database_api
from services.database_api import (
    get_all_attractions,
    get_attraction_by_id,
    create_attraction,
    update_attraction,
    delete_attraction
)


normal_bp = Blueprint(
    "normal_ui",
    __name__
)


@normal_bp.route("/api/attractions", methods=["GET"])
def get_attractions():

    search = request.args.get("search")
    city = request.args.get("city")
    category = request.args.get("category")
    max_price = request.args.get("max_price")

    if max_price:
        try:
            max_price = float(max_price)
        except ValueError:
            return jsonify({
                "error": "max_price must be a number"
            }), 400

    attractions = get_all_attractions(
        search=search,
        city=city,
        category=category,
        max_price=max_price
    )

    return jsonify(attractions)


@normal_bp.route("/api/attractions/<int:attraction_id>", methods=["GET"])
def get_attraction(attraction_id):

    attraction = get_attraction_by_id(attraction_id)

    if attraction is None:
        return jsonify({"error": "Attraction not found"}), 404

    return jsonify(attraction)


@normal_bp.route("/api/attractions", methods=["POST"])
def create():

    data = request.get_json(silent=True) or {}

    required_fields = ["name", "category", "city", "price"]

    for field in required_fields:
        if field not in data:
            return jsonify({
                "error": f"Missing required field: {field}"
            }), 400

    attraction = create_attraction(data)

    return jsonify(attraction), 201


@normal_bp.route("/api/attractions/<int:attraction_id>", methods=["PUT"])
def update(attraction_id):

    data = request.get_json(silent=True) or {}

    attraction = update_attraction(attraction_id, data)

    if attraction is None:
        return jsonify({"error": "Attraction not found"}), 404

    return jsonify(attraction)


@normal_bp.route("/api/attractions/<int:attraction_id>", methods=["DELETE"])
def delete(attraction_id):

    success = delete_attraction(attraction_id)

    if not success:
        return jsonify({"error": "Attraction not found"}), 404

    return jsonify({"message": "Attraction deleted successfully"})


@normal_bp.route(
    "/api/attractions/<int:attraction_id>/reviews",
    methods=["GET"]
)
def get_attraction_reviews(attraction_id):

    try:
        reviews = database_api.get_reviews(attraction_id)
        return jsonify(reviews), 200

    except requests.RequestException:
        return jsonify({
            "error": "Database service unavailable"
        }), 503


@normal_bp.route(
    "/api/attractions/<int:attraction_id>/reviews",
    methods=["POST"]
)
def add_attraction_review(attraction_id):

    data = request.get_json(silent=True) or {}

    if "rating" not in data:
        return jsonify({
            "error": "Missing required field: rating"
        }), 400

    try:
        reviews = database_api.create_review(attraction_id, data)

        if reviews is None:
            return jsonify({"error": "Attraction not found"}), 404

        return jsonify(reviews), 201

    except requests.RequestException:
        return jsonify({
            "error": "Database service unavailable"
        }), 503
