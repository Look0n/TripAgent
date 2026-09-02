import json

import requests

from flask import Blueprint, jsonify, request

from services import database_api
from services.llm_client import generate_response
from services.prompt_loader import load_recommendation_prompts


ai_mode_bp = Blueprint(
    "ai_mode",
    __name__
)


LOW_SEAT_THRESHOLD = 10


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
            "warnings": ["Search returned an empty result set"]
        }

    prices = [flight["price"] for flight in flights]
    durations = [flight["duration"] for flight in flights]

    limited_availability = [
        f"{flight['airline']} (flight {flight['flight_id']}) has {flight['seat_availability']} seats left"
        for flight in flights
        if flight["seat_availability"] < LOW_SEAT_THRESHOLD
    ]

    summary_lines = [
        f"{len(flights)} flights retrieved.",
        f"Price range: ${min(prices):.2f} to ${max(prices):.2f}.",
        f"Duration range: {min(durations)} to {max(durations)} minutes.",
        f"Traveller priority resolved as: {priority}."
    ]

    return {
        "flights_found": len(flights),
        "cheapest_price": min(prices),
        "most_expensive_price": max(prices),
        "shortest_duration": min(durations),
        "longest_duration": max(durations),
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


@ai_mode_bp.route("/api/flight/ai/recommend", methods=["POST"])
def recommend_flights():
    data = request.get_json(silent=True) or {}

    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({
            "error": "Message is required"
        }), 400

    origin = data.get("origin")
    destination = data.get("destination")

    plan = plan_search(message, origin, destination)

    try:
        response = database_api.list_flights(origin, destination)

    except requests.RequestException:
        return jsonify({
            "error": "Flight database unavailable"
        }), 503

    if response.status_code != 200:
        return jsonify({
            "error": "Could not retrieve flights"
        }), response.status_code

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

    except Exception:
        return jsonify({
            "error": "AI service is currently unavailable",
            "plan": plan,
            "act": {"flights_retrieved": len(flights)},
            "observe": observation
        }), 503

    return jsonify({
        "plan": plan,
        "act": {
            "flights_retrieved": len(flights),
            "source": "flight-database microservice"
        },
        "observe": observation,
        "adapt": recommendation,
        "flights": flights
    }), 200