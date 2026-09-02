from flask import Blueprint, jsonify, request
import json
import requests

from services.database_api import (
    search_for_recommendation
)

from services.llm_client import generate_text

from services.prompt_loader import (
    build_extraction_prompt,
    build_chat_recommendation_prompt
)


ai_bp = Blueprint(
    "ai_mode",
    __name__
)


@ai_bp.route(
    "/api/accommodations/recommend",
    methods=["POST"]
)
def accommodation_chat():

    data = request.get_json()

    if not data or not data.get("message"):
        return jsonify({
            "error": "Message is required."
        }), 400

    user_message = data["message"]


    # PLAN

    print("\nPLAN")
    print(
        "Understand the traveller's "
        "accommodation request."
    )

    extraction_prompt = (
        build_extraction_prompt(
            user_message
        )
    )

    try:
        extraction_text = generate_text(
            extraction_prompt,
            timeout=60,
            json_format=True,
            num_predict=150,
            temperature=0.1
        )
        
        print(
            "Raw extraction response:",
            extraction_text
        )

        requirements = json.loads(
            extraction_text
        )

    except (
        requests.RequestException,
        json.JSONDecodeError,
        KeyError
    ) as error:

        print(
            "Requirement extraction error:",
            repr(error)
        )

        return jsonify({
            "error":
                "Unable to understand "
                "the accommodation request."
        }), 503

    # Make sure preferences always exists

    if "preferences" not in requirements:
        requirements["preferences"] = []

    if requirements["preferences"] is None:
        requirements["preferences"] = []

    print(
        "Extracted requirements:",
        requirements
    )


    # ACT

    print("\nACT")
    print(
        "Searching accommodation database..."
    )

    # IMPORTANT:
    # We do NOT use type as a strict filter here.
    #
    # Example:
    # User asks for "resort-style accommodation"
    # but a Hotel may have a resort-style description.
    #
    # City / budget / guests are hard filters.
    # Type / vibe / family / CBD etc.
    # are considered later by the AI.

    guests = requirements.get("guests")

    if guests is not None:
        try:
            requirements["guests"] = int(guests)
        except (ValueError, TypeError):
            requirements["guests"] = None

    accommodations = search_for_recommendation(
        city=requirements.get("city"),
        budget=requirements.get("budget"),
        guests=requirements.get("guests"),
        accommodation_type=None
    )


    # OBSERVE

    print("\nOBSERVE")

    print(
        f"{len(accommodations)} "
        "matching accommodation(s) found.",
        "Candidate accommodations:",
        [
            item["accommodation_name"]
            for item in accommodations
        ]
    )

    if not accommodations:
        return jsonify({
            "reply":
                "I couldn't find an accommodation "
                "in the database that matches "
                "those requirements.",
            "requirements": requirements,
            "matches": 0
        }), 200


    # ADAPT

    print("\nADAPT")

    print(
        "Ranking database results using "
        "traveller preferences and "
        "accommodation descriptions..."
    )

    recommendation_prompt = (
        build_chat_recommendation_prompt(
            user_message,
            requirements,
            accommodations
        )
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
            "matches": len(accommodations)
        }), 200

    except requests.RequestException as error:

        print(
            "Recommendation error:",
            error
        )

        return jsonify({
            "error":
                "Unable to connect "
                "to the AI service."
        }), 503