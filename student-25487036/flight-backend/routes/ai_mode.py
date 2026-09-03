import json

import requests

from flask import Blueprint, jsonify, request

from services import database_api
from services.llm_client import generate_response
from services.prompt_loader import load_recommendation_prompts
from views.html_formatters import (
    format_agentic_response,
    format_flight_cards
)


ai_mode_bp = Blueprint(
    "ai_mode",
    __name__
)


LOW_SEAT_THRESHOLD = 10

HTML_HEADERS = {"Content-Type": "text/html; charset=utf-8"}


class DatabaseUnavailable(Exception):
    pass


def plan_search(message, origin, destination):
    lowered = message.lower()

    if any(word in lowered for word in ["cheap", "budget", "affordable", "low cost"]):
        priority = "price"

    elif any(word in lowered for word in ["fast", "quick", "shortest", "direct"]):
        priority = "duration"

    else:
        priority = "balanced"

    return {
        "goal": "Recommend a suitable flight from the TripAgent flight database",
        "origin": origin,
        "destination": destination,
        "priority": priority,
        "steps": [
            "Retrieve matching flights from the flight database service",
            "Verify the retrieved data deterministically",
            "Generate a grounded recommendation using the local LLM"
        ]
    }


def observe_flights(flights, priority):
    if not flights:
        return {
            "flights_found": 0,
            "summary": "No flights matched the requested route.",
            "warnings": ["Search returned an empty result set"],
            "limited_availability": []
        }

    prices = [flight["price"] for flight in flights]
    durations = [flight["duration"] for flight in flights]

    cheapest = min(flights, key=lambda flight: flight["price"])
    quickest = min(flights, key=lambda flight: flight["duration"])

    limited_availability = [
        f"{flight['airline']} (flight {flight['flight_id']}) has {flight['seat_availability']} seats left"
        for flight in flights
        if flight["seat_availability"] < LOW_SEAT_THRESHOLD
    ]

    summary_lines = [
        f"{len(flights)} flights retrieved.",
        f"Price range: ${min(prices):.2f} to ${max(prices):.2f}.",
        f"Duration range: {min(durations)} to {max(durations)} minutes.",
        f"Cheapest: {cheapest['airline']}, flight {cheapest['flight_id']}, ${cheapest['price']:.2f}.",
        f"Quickest: {quickest['airline']}, flight {quickest['flight_id']}, {quickest['duration']} minutes.",
        f"Traveller priority resolved as: {priority}."
    ]

    return {
        "flights_found": len(flights),
        "cheapest_price": min(prices),
        "most_expensive_price": max(prices),
        "shortest_duration": min(durations),
        "longest_duration": max(durations),
        "cheapest_flight_id": cheapest["flight_id"],
        "quickest_flight_id": quickest["flight_id"],
        "limited_availability": limited_availability,
        "summary": " ".join(summary_lines),
        "warnings": limited_availability
    }


def format_flights_for_prompt(flights):
    trimmed = [
        {
            "flight_id": flight["flight_id"],
            "airline": flight["airline"],
            "origin": flight["origin"],
            "destination": flight["destination"],
            "departure_time": flight["departure_time"],
            "price": flight["price"],
            "duration": flight["duration"],
            "seat_availability": flight["seat_availability"]
        }
        for flight in flights
    ]

    return json.dumps(trimmed, indent=2)


def run_agentic_loop(message, origin, destination):
    plan = plan_search(message, origin, destination)

    try:
        response = database_api.list_flights(origin, destination)

    except requests.RequestException:
        raise DatabaseUnavailable("Flight database service did not respond")

    if response.status_code != 200:
        raise DatabaseUnavailable("Flight database returned an error")

    flights = response.json()

    observation = observe_flights(flights, plan["priority"])

    system_prompt, user_prompt = load_recommendation_prompts(
        message=message,
        priority=plan["priority"],
        observation=observation["summary"],
        flights=format_flights_for_prompt(flights)
    )

    try:
        recommendation = generate_response(system_prompt, user_prompt)
        ai_available = True

    except Exception:
        recommendation = (
            "The recommendation model is unavailable. "
            "The verified flight data below was still retrieved successfully."
        )
        ai_available = False

    return {
        "plan": plan,
        "act": {
            "flights_retrieved": len(flights),
            "source": "flight-database microservice"
        },
        "observe": observation,
        "adapt": recommendation,
        "ai_available": ai_available,
        "flights": flights
    }


@ai_mode_bp.route("/api/flight/ai/recommend", methods=["POST"])
def recommend_flights():
    data = request.get_json(silent=True) or {}

    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({
            "error": "Message is required"
        }), 400

    try:
        result = run_agentic_loop(
            message,
            data.get("origin"),
            data.get("destination")
        )

    except DatabaseUnavailable:
        return jsonify({
            "error": "Flight database unavailable"
        }), 503

    return jsonify(result), 200


@ai_mode_bp.route("/api/flight/ai/recommend/html", methods=["POST"])
def recommend_flights_html():
    message = str(request.form.get("message", "")).strip()

    if not message:
        return (
            '<p class="warning">Please describe what you are looking for.</p>',
            400,
            HTML_HEADERS
        )

    try:
        result = run_agentic_loop(
            message,
            request.form.get("origin"),
            request.form.get("destination")
        )

    except DatabaseUnavailable:
        return (
            '<p class="warning">The flight database is currently unavailable.</p>',
            503,
            HTML_HEADERS
        )

    body = format_agentic_response(
        result["plan"],
        result["act"],
        result["observe"],
        result["adapt"]
    ) + format_flight_cards(result["flights"])

    return body, 200, HTML_HEADERS