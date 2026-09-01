import requests

from flask import Blueprint, jsonify, request, session
from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)

from services.database_api import (
    create_customer,
    delete_preferences,
    get_customer,
    get_customer_by_email,
    get_preferences,
    save_preferences,
    update_customer
)


normal_ui_bp = Blueprint(
    "normal_ui",
    __name__
)


def current_customer_id():

    gateway_customer_id = request.headers.get(
        "X-Customer-ID"
    )

    if gateway_customer_id:

        try:
            return int(
                gateway_customer_id
            )

        except ValueError:
            return None

    return session.get(
        "customer_id"
    )


def login_required():
    customer_id = current_customer_id()

    if customer_id is None:
        return None, (
            jsonify({
                "error": "Authentication required"
            }),
            401
        )

    return customer_id, None


@normal_ui_bp.route(
    "/api/account/register",
    methods=["POST"]
)
def register():
    data = request.get_json(silent=True) or {}

    required_fields = [
        "first_name",
        "last_name",
        "email",
        "password"
    ]

    missing_fields = [
        field
        for field in required_fields
        if not str(data.get(field, "")).strip()
    ]

    if missing_fields:
        return jsonify({
            "error": "Missing required fields",
            "fields": missing_fields
        }), 400

    password = data["password"]

    if len(password) < 8:
        return jsonify({
            "error":
                "Password must contain at least 8 characters"
        }), 400

    customer_data = {
        "first_name":
            data["first_name"].strip(),

        "last_name":
            data["last_name"].strip(),

        "email":
            data["email"].strip().lower(),

        "password":
            generate_password_hash(password),

        "phone":
            data.get("phone", "").strip(),

        "country":
            data.get("country", "").strip()
    }

    try:
        response = create_customer(
            customer_data
        )

    except requests.RequestException:
        return jsonify({
            "error":
                "Account database service is unavailable"
        }), 503

    response_data = response.json()

    if response.status_code == 201:
        session["customer_id"] = response_data[
            "customer_id"
        ]

    return jsonify(
        response_data
    ), response.status_code


@normal_ui_bp.route(
    "/api/account/login",
    methods=["POST"]
)
def login():
    data = request.get_json(silent=True) or {}

    email = str(
        data.get("email", "")
    ).strip().lower()

    password = str(
        data.get("password", "")
    )

    if not email or not password:
        return jsonify({
            "error":
                "Email and password are required"
        }), 400

    try:
        response = get_customer_by_email(
            email
        )

    except requests.RequestException:
        return jsonify({
            "error":
                "Account database service is unavailable"
        }), 503

    if response.status_code != 200:
        return jsonify({
            "error":
                "Invalid email or password"
        }), 401

    customer = response.json()

    if not check_password_hash(
        customer["password"],
        password
    ):
        return jsonify({
            "error":
                "Invalid email or password"
        }), 401

    session["customer_id"] = customer[
        "customer_id"
    ]

    return jsonify({
        "message": "Login successful",
        "customer_id":
            customer["customer_id"],
        "first_name":
            customer["first_name"]
    }), 200


@normal_ui_bp.route(
    "/api/account/logout",
    methods=["POST"]
)
def logout():
    session.clear()

    return jsonify({
        "message": "Logout successful"
    }), 200


@normal_ui_bp.route(
    "/api/account/session",
    methods=["GET"]
)
def session_status():
    customer_id = current_customer_id()

    return jsonify({
        "authenticated":
            customer_id is not None,

        "customer_id":
            customer_id
    }), 200


@normal_ui_bp.route(
    "/api/account/profile",
    methods=["GET"]
)
def profile():
    customer_id, error = login_required()

    if error:
        return error

    try:
        response = get_customer(
            customer_id
        )

    except requests.RequestException:
        return jsonify({
            "error":
                "Account database service is unavailable"
        }), 503

    return jsonify(
        response.json()
    ), response.status_code


@normal_ui_bp.route(
    "/api/account/profile",
    methods=["PUT"]
)
def edit_profile():
    customer_id, error = login_required()

    if error:
        return error

    data = request.get_json(
        silent=True
    ) or {}

    allowed_fields = {
        "first_name",
        "last_name",
        "phone",
        "country"
    }

    profile_data = {
        key: value
        for key, value in data.items()
        if key in allowed_fields
    }

    try:
        response = update_customer(
            customer_id,
            profile_data
        )

    except requests.RequestException:
        return jsonify({
            "error":
                "Account database service is unavailable"
        }), 503

    return jsonify(
        response.json()
    ), response.status_code


@normal_ui_bp.route(
    "/api/account/preferences",
    methods=["GET"]
)
def preferences():
    customer_id, error = login_required()

    if error:
        return error

    try:
        response = get_preferences(
            customer_id
        )

    except requests.RequestException:
        return jsonify({
            "error":
                "Account database service is unavailable"
        }), 503

    if response.status_code == 404:
        return jsonify({
            "preference_id": None,
            "customer_id": customer_id,
            "budget_level": "",
            "travel_style": "",
            "accommodation_type": "",
            "transport_preference": "",
            "food_preference": "",
            "pace_preference": ""
        }), 200

    return jsonify(
        response.json()
    ), response.status_code


@normal_ui_bp.route(
    "/api/account/preferences",
    methods=["PUT"]
)
def edit_preferences():
    customer_id, error = login_required()

    if error:
        return error

    data = request.get_json(
        silent=True
    ) or {}

    allowed_fields = {
        "budget_level",
        "travel_style",
        "accommodation_type",
        "transport_preference",
        "food_preference",
        "pace_preference"
    }

    preference_data = {
        key: value
        for key, value in data.items()
        if key in allowed_fields
    }

    try:
        response = save_preferences(
            customer_id,
            preference_data
        )

    except requests.RequestException:
        return jsonify({
            "error":
                "Account database service is unavailable"
        }), 503

    return jsonify(
        response.json()
    ), response.status_code


@normal_ui_bp.route(
    "/api/account/preferences",
    methods=["DELETE"]
)
def remove_preferences():
    customer_id, error = login_required()

    if error:
        return error

    try:
        response = delete_preferences(
            customer_id
        )

    except requests.RequestException:
        return jsonify({
            "error":
                "Account database service is unavailable"
        }), 503

    return jsonify(
        response.json()
    ), response.status_code