import requests

from flask import Blueprint, jsonify, request

from services import database_api


normal_bp = Blueprint(
    "normal_ui",
    __name__
)


FILTER_FIELDS = (
    "item_type",
    "category",
    "priority",
    "is_completed"
)


def forward_database_response(response):
    try:
        payload = response.json()

    except ValueError:
        return jsonify({
            "error": "Invalid response from checklist database"
        }), 502

    return jsonify(payload), response.status_code


def database_unavailable_response():
    return jsonify({
        "error": "Checklist database service is unavailable"
    }), 503


@normal_bp.route(
    "/api/checklist-items",
    methods=["GET"]
)
def get_checklist_items():
    params = {
        field: request.args.get(field)
        for field in FILTER_FIELDS
        if request.args.get(field) is not None
    }

    try:
        response = database_api.get_checklist_items(params)

    except requests.RequestException:
        return database_unavailable_response()

    return forward_database_response(response)


@normal_bp.route(
    "/api/checklist-items/<int:item_id>",
    methods=["GET"]
)
def get_checklist_item(item_id):
    try:
        response = database_api.get_checklist_item(item_id)

    except requests.RequestException:
        return database_unavailable_response()

    return forward_database_response(response)


@normal_bp.route(
    "/api/checklist-items",
    methods=["POST"]
)
def create_checklist_item():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "A JSON object is required"
        }), 400

    try:
        response = database_api.create_checklist_item(data)

    except requests.RequestException:
        return database_unavailable_response()

    return forward_database_response(response)


@normal_bp.route(
    "/api/checklist-items/<int:item_id>",
    methods=["PUT"]
)
def update_checklist_item(item_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not data:
        return jsonify({
            "error": "A non-empty JSON object is required"
        }), 400

    try:
        response = database_api.update_checklist_item(
            item_id,
            data
        )

    except requests.RequestException:
        return database_unavailable_response()

    return forward_database_response(response)


@normal_bp.route(
    "/api/checklist-items/<int:item_id>",
    methods=["DELETE"]
)
def delete_checklist_item(item_id):
    try:
        response = database_api.delete_checklist_item(item_id)

    except requests.RequestException:
        return database_unavailable_response()

    return forward_database_response(response)
