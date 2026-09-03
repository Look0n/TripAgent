import requests

from flask import Blueprint, jsonify, request

from services import database_api

from views.html_formatters import format_flight_table

from views.html_formatters import format_flight_table, format_flight_edit_row

normal_ui_bp = Blueprint(
    "normal_ui",
    __name__
)

HTML_HEADERS = {"Content-Type": "text/html; charset=utf-8"}


def normalise_timestamp(value):
    if len(value) == 16:
        return f"{value}:00"

    return value




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


def fetch_flight_table():
    response = database_api.list_flights()

    if response.status_code != 200:
        return '<p class="warning">Could not load flights.</p>'

    return format_flight_table(response.json())


@normal_ui_bp.route("/api/flight/flights/html", methods=["GET"])
def list_flights_html():
    try:
        body = fetch_flight_table()

    except requests.RequestException:
        return (
            '<p class="warning">Flight database unavailable.</p>',
            503,
            HTML_HEADERS
        )

    return body, 200, HTML_HEADERS


@normal_ui_bp.route("/api/flight/flights/html", methods=["POST"])
def create_flight_html():
    required_fields = [
        "airline",
        "origin",
        "destination",
        "departure_time",
        "arrival_time",
        "price",
        "duration",
        "seat_availability"
    ]

    missing_fields = [
        field
        for field in required_fields
        if not request.form.get(field)
    ]

    if missing_fields:
        return (
            f'<p class="warning">Missing fields: '
            f'{", ".join(missing_fields)}</p>',
            400,
            HTML_HEADERS
        )

    payload = {
        "airline": request.form["airline"],
        "origin": request.form["origin"].upper(),
        "destination": request.form["destination"].upper(),
        "departure_time": normalise_timestamp(request.form["departure_time"]),
        "arrival_time": normalise_timestamp(request.form["arrival_time"]),
        "price": float(request.form["price"]),
        "duration": int(request.form["duration"]),
        "image": request.form.get("image") or None,
        "seat_availability": int(request.form["seat_availability"])
    }

    try:
        response = database_api.create_flight(payload)

        if response.status_code == 409:
            return (
                '<p class="warning">That flight already exists.</p>'
                + fetch_flight_table(),
                200,
                HTML_HEADERS
            )

        body = fetch_flight_table()

    except requests.RequestException:
        return (
            '<p class="warning">Flight database unavailable.</p>',
            503,
            HTML_HEADERS
        )

    return body, 200, HTML_HEADERS


@normal_ui_bp.route("/api/flight/flights/<int:flight_id>/html", methods=["DELETE"])
def delete_flight_html(flight_id):
    try:
        database_api.delete_flight(flight_id)

        body = fetch_flight_table()

    except requests.RequestException:
        return (
            '<p class="warning">Flight database unavailable.</p>',
            503,
            HTML_HEADERS
        )

    return body, 200, HTML_HEADERS


@normal_ui_bp.route("/api/flight/flights/<int:flight_id>/edit", methods=["GET"])
def edit_flight_form(flight_id):
    try:
        response = database_api.get_flight(flight_id)

        if response.status_code != 200:
            return (
                '<tr><td colspan="8" class="warning">'
                'Flight not found.</td></tr>',
                200,
                HTML_HEADERS
            )

        body = format_flight_edit_row(response.json())

    except requests.RequestException:
        return (
            '<tr><td colspan="8" class="warning">'
            'Flight database unavailable.</td></tr>',
            503,
            HTML_HEADERS
        )

    return body, 200, HTML_HEADERS


@normal_ui_bp.route("/api/flight/flights/<int:flight_id>/html", methods=["PUT"])
def update_flight_html(flight_id):
    required_fields = [
        "airline",
        "origin",
        "destination",
        "departure_time",
        "arrival_time",
        "price",
        "duration",
        "seat_availability"
    ]

    missing_fields = [
        field
        for field in required_fields
        if not request.form.get(field)
    ]

    if missing_fields:
        return (
            f'<p class="warning">Missing fields: '
            f'{", ".join(missing_fields)}</p>'
            + fetch_flight_table(),
            200,
            HTML_HEADERS
        )

    payload = {
        "airline": request.form["airline"],
        "origin": request.form["origin"].upper(),
        "destination": request.form["destination"].upper(),
        "departure_time": normalise_timestamp(request.form["departure_time"]),
        "arrival_time": normalise_timestamp(request.form["arrival_time"]),
        "price": float(request.form["price"]),
        "duration": int(request.form["duration"]),
        "image": request.form.get("image") or None,
        "seat_availability": int(request.form["seat_availability"])
    }

    try:
        response = database_api.update_flight(flight_id, payload)

        if response.status_code == 404:
            return (
                '<p class="warning">That flight no longer exists.</p>'
                + fetch_flight_table(),
                200,
                HTML_HEADERS
            )

        if response.status_code == 409:
            return (
                '<p class="warning">Another flight already has that '
                'airline, route and departure time.</p>'
                + fetch_flight_table(),
                200,
                HTML_HEADERS
            )

        body = fetch_flight_table()

    except requests.RequestException:
        return (
            '<p class="warning">Flight database unavailable.</p>',
            503,
            HTML_HEADERS
        )

    return body, 200, HTML_HEADERS