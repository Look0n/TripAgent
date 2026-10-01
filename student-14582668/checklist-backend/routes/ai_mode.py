import json

import requests

from flask import Blueprint, jsonify, request

from services import database_api
from services.llm_client import generate_text
from services.prompt_loader import (
    build_checklist_recommendation_prompt
)


ai_bp = Blueprint(
    "ai_mode",
    __name__
)


VALID_ITEM_TYPES = {
    "task",
    "packing"
}

VALID_PRIORITIES = {
    "high": "High",
    "medium": "Medium",
    "low": "Low"
}

MAX_SUGGESTIONS = 5


def clean_suggestions(suggestions, existing_items):
    if not isinstance(suggestions, list):
        raise ValueError("AI suggestions must be a list")

    existing_titles = {
        str(item.get("title", "")).strip().casefold()
        for item in existing_items
        if isinstance(item, dict)
    }

    accepted_titles = set()
    cleaned = []

    for suggestion in suggestions:
        if not isinstance(suggestion, dict):
            continue

        title = suggestion.get("title")
        item_type = suggestion.get("item_type")
        priority = suggestion.get("priority")

        if not isinstance(title, str) or not title.strip():
            continue

        if not isinstance(item_type, str):
            continue

        item_type = item_type.strip().lower()

        if item_type not in VALID_ITEM_TYPES:
            continue

        if not isinstance(priority, str):
            continue

        priority = VALID_PRIORITIES.get(
            priority.strip().lower()
        )

        if priority is None:
            continue

        normalised_title = title.strip().casefold()

        if (
            normalised_title in existing_titles
            or normalised_title in accepted_titles
        ):
            continue

        category = suggestion.get("category")
        description = suggestion.get("description")

        if category is not None and not isinstance(category, str):
            category = None

        if description is not None and not isinstance(
            description,
            str
        ):
            description = None

        cleaned.append({
            "title": title.strip(),
            "item_type": item_type,
            "category": (
                category.strip()
                if isinstance(category, str)
                else None
            ),
            "description": (
                description.strip()
                if isinstance(description, str)
                else None
            ),
            "priority": priority
        })

        accepted_titles.add(normalised_title)

        if len(cleaned) == MAX_SUGGESTIONS:
            break

    return cleaned


@ai_bp.route(
    "/api/checklist-items/recommend",
    methods=["POST"]
)
def recommend_checklist_items():
    data = request.get_json(silent=True) or {}
    message = data.get("message")

    if not isinstance(message, str) or not message.strip():
        return jsonify({
            "error": "Message is required"
        }), 400

    message = message.strip()

    # PLAN
    print("\nPLAN")
    print("Understand the traveller's preparation request.")

    # ACT
    print("\nACT")
    print("Retrieve the traveller's existing checklist items.")

    try:
        database_response = database_api.get_checklist_items()

    except requests.RequestException:
        return jsonify({
            "error": "Checklist database service is unavailable"
        }), 503

    if database_response.status_code != 200:
        return jsonify({
            "error": "Unable to retrieve existing checklist items"
        }), 503

    try:
        existing_items = database_response.json()

    except ValueError:
        return jsonify({
            "error": "Invalid response from checklist database"
        }), 502

    if not isinstance(existing_items, list):
        return jsonify({
            "error": "Invalid response from checklist database"
        }), 502

    # OBSERVE
    print("\nOBSERVE")
    print(
        f"Found {len(existing_items)} existing checklist item(s)."
    )

    prompt = build_checklist_recommendation_prompt(
        message,
        existing_items
    )

    # ADAPT
    print("\nADAPT")
    print("Generate useful checklist items that are still missing.")

    try:
        generated_text = generate_text(prompt)
        generated_data = json.loads(generated_text)

        if not isinstance(generated_data, dict):
            raise ValueError("AI response must be a JSON object")

        suggestions = clean_suggestions(
            generated_data.get("suggestions"),
            existing_items
        )

    except requests.RequestException:
        return jsonify({
            "error": "AI service is currently unavailable"
        }), 503

    except (json.JSONDecodeError, TypeError, ValueError):
        return jsonify({
            "error": "AI service returned an invalid response"
        }), 502

    reply = generated_data.get("reply")

    if not isinstance(reply, str) or not reply.strip():
        reply = "Here are some additional checklist suggestions."

    return jsonify({
        "reply": reply.strip(),
        "existing_items_count": len(existing_items),
        "suggestions": suggestions
    }), 200
