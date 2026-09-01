import os

import requests

from flask import (
    Blueprint,
    jsonify,
    make_response,
    request
)

from services.database_api import (
    create_session,
    delete_session,
    get_session
)


access_bp = Blueprint(
    "access",
    __name__
)


ACCOUNT_BACKEND_URL = os.getenv(
    "ACCOUNT_BACKEND_URL",
    "http://account-backend:5001"
)


COOKIE_NAME = "tripagent_session"


def set_session_cookie(
    response,
    session_id
):

    response.set_cookie(
        COOKIE_NAME,
        session_id,
        httponly=True,
        samesite="Lax",
        secure=False,
        max_age=86400
    )


@access_bp.route(
    "/api/access/register",
    methods=["POST"]
)
def register():

    data = request.get_json(
        silent=True
    ) or {}

    try:
        account_response = requests.post(
            f"{ACCOUNT_BACKEND_URL}/api/account/register",
            json=data,
            timeout=5
        )

    except requests.RequestException:

        return jsonify({
            "error":
                "Account service unavailable"
        }), 503

    account_data = account_response.json()

    if account_response.status_code != 201:

        return jsonify(
            account_data
        ), account_response.status_code

    customer_id = account_data.get(
        "customer_id"
    )

    try:
        session_response = create_session(
            customer_id
        )

    except requests.RequestException:

        return jsonify({
            "error":
                "Session service unavailable"
        }), 503

    session_data = session_response.json()

    response = make_response(
        jsonify({
            "message":
                "Registration successful",

            "customer_id":
                customer_id
        }),
        201
    )

    set_session_cookie(
        response,
        session_data["session_id"]
    )

    return response


@access_bp.route(
    "/api/access/login",
    methods=["POST"]
)
def login():

    data = request.get_json(
        silent=True
    ) or {}

    try:
        account_response = requests.post(
            f"{ACCOUNT_BACKEND_URL}/api/account/login",
            json=data,
            timeout=5
        )

    except requests.RequestException:

        return jsonify({
            "error":
                "Account service unavailable"
        }), 503

    account_data = account_response.json()

    if account_response.status_code != 200:

        return jsonify(
            account_data
        ), account_response.status_code

    customer_id = account_data[
        "customer_id"
    ]

    try:
        session_response = create_session(
            customer_id
        )

    except requests.RequestException:

        return jsonify({
            "error":
                "Session service unavailable"
        }), 503

    session_data = session_response.json()

    response = make_response(
        jsonify({
            "message": "Login successful",
            "customer_id": customer_id,
            "first_name":
                account_data.get("first_name")
        }),
        200
    )

    set_session_cookie(
        response,
        session_data["session_id"]
    )

    return response


@access_bp.route(
    "/api/access/logout",
    methods=["POST"]
)
def logout():

    session_id = request.cookies.get(
        COOKIE_NAME
    )

    if session_id:

        try:
            delete_session(
                session_id
            )

        except requests.RequestException:
            pass

    response = make_response(
        jsonify({
            "message": "Logout successful"
        }),
        200
    )

    response.delete_cookie(
        COOKIE_NAME
    )

    return response


@access_bp.route(
    "/api/access/session",
    methods=["GET"]
)
def session_status():

    session_id = request.cookies.get(
        COOKIE_NAME
    )

    if not session_id:

        return jsonify({
            "authenticated": False
        }), 200

    try:
        session_response = get_session(
            session_id
        )

    except requests.RequestException:

        return jsonify({
            "authenticated": False
        }), 200

    if session_response.status_code != 200:

        return jsonify({
            "authenticated": False
        }), 200

    session_data = session_response.json()

    return jsonify({
        "authenticated": True,
        "customer_id":
            session_data["customer_id"]
    }), 200