import requests

from flask import (
    Blueprint,
    Response,
    jsonify,
    request
)

from services.database_api import (
    get_session
)

from services.service_router import (
    get_service_url
)


gateway_bp = Blueprint(
    "gateway",
    __name__
)


COOKIE_NAME = "tripagent_session"


def validate_session():

    session_id = request.cookies.get(
        COOKIE_NAME
    )

    if not session_id:
        return None

    try:
        response = get_session(
            session_id
        )

    except requests.RequestException:
        return None

    if response.status_code != 200:
        return None

    return response.json()


def forward_request(
    service_name,
    path,
    customer_id
):

    service_url = get_service_url(
        service_name
    )

    if not service_url:

        return jsonify({
            "error": "Unknown service"
        }), 404

    target_url = (
        f"{service_url}/api/"
        f"{service_name}/{path}"
    )

    headers = {
        "X-Customer-ID":
            str(customer_id)
    }

    content_type = request.headers.get(
        "Content-Type"
    )

    if content_type:
        headers["Content-Type"] = content_type

    try:
        response = requests.request(
            method=request.method,
            url=target_url,
            params=request.args,
            data=request.get_data(),
            headers=headers,
            timeout=120
        )

    except requests.RequestException:

        return jsonify({
            "error":
                f"{service_name} service unavailable"
        }), 503

    excluded_headers = {
        "content-encoding",
        "content-length",
        "transfer-encoding",
        "connection"
    }

    response_headers = [
        (key, value)
        for key, value
        in response.headers.items()
        if key.lower()
        not in excluded_headers
    ]

    return Response(
        response.content,
        response.status_code,
        response_headers
    )


@gateway_bp.route(
    "/api/account/<path:path>",
    methods=[
        "GET",
        "POST",
        "PUT",
        "DELETE"
    ]
)
def account_proxy(path):

    session_data = validate_session()

    if session_data is None:

        return jsonify({
            "error":
                "Authentication required"
        }), 401

    return forward_request(
        "account",
        path,
        session_data["customer_id"]
    )
@gateway_bp.route(
    "/api/accommodation/<path:path>",
    methods=[
        "GET",
        "POST",
        "PUT",
        "DELETE"
    ]
)
def accommodation_proxy(path):

    session_data = validate_session()

    if session_data is None:

        return jsonify({
            "error":
                "Authentication required"
        }), 401

    service_url = get_service_url(
        "accommodation"
    )

    if not service_url:

        return jsonify({
            "error":
                "Accommodation service unavailable"
        }), 503

@gateway_bp.route(
    "/api/flight/<path:path>",
    methods=[
        "GET",
        "POST",
        "PUT",
        "DELETE"
    ]
)
def flight_proxy(path):

    session_data = validate_session()

    customer_id = (
        session_data["customer_id"]
        if session_data
        else "anonymous"
    )

    return forward_request(
        "flight",
        path,
        customer_id
    )

    # Browser:
    # /api/accommodation/accommodations/123
    #
    # Backend:
    # /api/accommodations/123
    target_url = (
        f"{service_url}/api/{path}"
    )

    headers = {
        "X-Customer-ID":
            str(session_data["customer_id"]),

        "Content-Type":
            request.headers.get(
                "Content-Type",
                "application/json"
            )
    }

    try:

        response = requests.request(
            method=request.method,
            url=target_url,
            params=request.args,
            json=request.get_json(
                silent=True
            ),
            headers=headers,
            timeout=10
        )

    except requests.RequestException:

        return jsonify({
            "error":
                "Accommodation service unavailable"
        }), 503

    excluded_headers = {
        "content-encoding",
        "content-length",
        "transfer-encoding",
        "connection"
    }

    response_headers = [
        (key, value)
        for key, value
        in response.headers.items()
        if key.lower()
        not in excluded_headers
    ]

    return Response(
        response.content,
        response.status_code,
        response_headers
    )