from flask import Blueprint, jsonify, request
import json
import requests

from services.database_api import search_for_recommendation
from services.llm_client import generate_text
from services.prompt_loader import (
    build_extraction_prompt,
    build_chat_recommendation_prompt
)


ai_bp = Blueprint(
    "ai_mode",
    __name__
)


@ai_bp.route("/api/attractions/recommend", methods=["POST"])
def attractions_chat():

    data = request.get_json(silent=True) or {}

    user_message = data.get("message") or data.get("prompt")

    if not user_message:
        return jsonify({
            "error": "Message is required."
        }), 400

    # PLAN

    extraction_prompt = build_extraction_prompt(user_message)

    try:
        extraction_text = generate_text(
            extraction_prompt,
            timeout=60,
            json_format=True,
            num_predict=150,
            temperature=0.1
        )

        requirements = json.loads(extraction_text)

    except (
        requests.RequestException,
        json.JSONDecodeError,
        KeyError
    ) as error:

        print("Requirement extraction error:", repr(error))

        return jsonify({
            "error": "Unable to understand the attraction request."
        }), 503

    if not requirements.get("preferences"):
        requirements["preferences"] = []

    # ACT

    try:
        attractions = search_for_recommendation(
            city=requirements.get("city"),
            category=requirements.get("category"),
            max_price=requirements.get("budget")
        )

    except requests.RequestException:
        return jsonify({
            "error": "Attractions database is unavailable."
        }), 503

    # OBSERVE

    if not attractions:
        return jsonify({
            "reply": (
                "I couldn't find an attraction in the database "
                "that matches those requirements."
            ),
            "requirements": requirements,
            "matches": 0
        }), 200

    # ADAPT

    recommendation_prompt = build_chat_recommendation_prompt(
        user_message,
        requirements,
        attractions
    )

    try:
        reply = generate_text(
            recommendation_prompt,
            timeout=120,
            num_predict=150,
            temperature=0.3
        )

        return jsonify({
            "reply": reply,
            "requirements": requirements,
            "matches": len(attractions)
        }), 200

    except requests.RequestException as error:
        print("Recommendation error:", error)

        return jsonify({
            "error": "Unable to connect to the AI service."
        }), 503
