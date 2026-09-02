import requests

from flask import Blueprint, jsonify, request

from services import database_api


normal_ui_bp = Blueprint(
    "normal_ui",
    __name__
)


@normal_ui_bp.route("/api/flight/flights", methods=["GET"])
def list_flights():
    origin = request.args.get("origin")
    destination = request.args.get("destination")

    try:
        response = database_api.list_flights(
            origin,
            destination
        )

    except requests.RequestException:
        return jsonify({
            "error": "Flight database unavailable"
        }), 503

    return jsonify(response.json()), response.status_code


@normal_ui_bp.route("/api/flight/flights/<int:flight_id>", methods=["GET"])
def get_flight(flight_id):
    try:
        response = database_api.get_flight(flight_id)

    except requests.RequestException:
        return jsonify({
            "error": "Flight database unavailable"
        }), 503

    return jsonify(response.json()), response.status_code


@normal_ui_bp.route("/api/flight/flights", methods=["POST"])
def create_flight():
    data = request.get_json(silent=True) or {}

    try:
        response = database_api.create_flight(data)

    except requests.RequestException:
        return jsonify({
            "error": "Flight database unavailable"
        }), 503

    return jsonify(response.json()), response.status_code


@normal_ui_bp.route("/api/flight/flights/<int:flight_id>", methods=["PUT"])
def update_flight(flight_id):
    data = request.get_json(silent=True) or {}

    try:
        response = database_api.update_flight(
            flight_id,
            data
        )

    except requests.RequestException:
        return jsonify({
            "error": "Flight database unavailable"
        }), 503

    return jsonify(response.json()), response.status_code


@normal_ui_bp.route("/api/flight/flights/<int:flight_id>", methods=["DELETE"])
def delete_flight(flight_id):
    try:
        response = database_api.delete_flight(flight_id)

    except requests.RequestException:
        return jsonify({
            "error": "Flight database unavailable"
        }), 503

    return jsonify(response.json()), response.status_code