import requests

from flask import Blueprint, jsonify, request

from services.llm_client import generate_response
from services.prompt_loader import load_preference_prompt
from views.html_formatters import format_ai_response


ai_mode_bp = Blueprint(
    "ai_mode",
    __name__
)


@ai_mode_bp.route(
    "/api/account/ai/preferences",
    methods=["POST"]
)
def preference_assistant():

    # Customer identity is validated by the shared gateway
    # and forwarded to the Account service.
    customer_id = request.headers.get(
        "X-Customer-ID"
    )

    if not customer_id:
        return jsonify({
            "error": "Authentication required"
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    message = str(
        data.get("message", "")
    ).strip()

    if not message:
        return jsonify({
            "error": "Message is required"
        }), 400

    prompt = load_preference_prompt(
        message
    )

    try:
        answer = generate_response(
            prompt
        )

    except requests.RequestException:
        return jsonify({
            "error":
                "AI service is currently unavailable"
        }), 503

    return jsonify({
        "response": answer,
        "html":
            format_ai_response(answer)
    }), 200