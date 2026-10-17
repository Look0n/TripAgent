import os
import re

from flask import Blueprint, jsonify, request
from requests import RequestException

from services.database_api import get_all_accommodations

from services.multi_agent_client import (
    check_multi_agent_health,
    run_multi_agent_workflow,
    submit_human_review,
    get_workflow
)

multi_agent_bp = Blueprint(
    "accommodation_multi_agent",
    __name__
)

# Match the existing MCP/RAG mode pattern: process-wide, OFF on startup.
# Cloud deployments can explicitly lock the feature off.
_multi_agent_enabled = False

def mode_enabled():
    return _multi_agent_enabled

def set_mode_enabled(enabled):
    global _multi_agent_enabled
    _multi_agent_enabled = bool(enabled)
    return _multi_agent_enabled

def mode_locked():
    return os.getenv("MULTI_AGENT_LOCKED", "false").lower() in ("true", "1", "yes", "on")

def permitted():
    if mode_locked():
        return (jsonify({"error": "Multi-Agent is locked off by deployment configuration"}), 403)
    if not mode_enabled():
        return (jsonify({"error": "Multi-Agent mode is OFF"}), 403)
    return None

def fail(exc):
    status_code = 503

    if getattr(exc, "response", None) is not None:
        status_code = exc.response.status_code

    return jsonify({
        "error": str(exc)
    }), status_code
    
def extract_accommodation_filters(user_request):
    text = user_request.lower()

    city = None
    max_price = None

    # Demo cities currently supported by accommodation data
    cities = [
        "Sydney",
        "Melbourne",
        "Brisbane",
        "Cairns",
        "Gold Coast",
        "Port Douglas",
        "Bathurst"
    ]

    for known_city in cities:
        if known_city.lower() in text:
            city = known_city
            break

    price_match = re.search(
        r"(?:under|below|max(?:imum)?)\s*\$?(\d+(?:\.\d+)?)",
        text
    )

    if price_match:
        max_price = float(
            price_match.group(1)
        )

    return city, max_price
    
    
# -----------------------------
# Mode control
# -----------------------------

@multi_agent_bp.route(
    "/api/accommodations/multi-agent/mode",
    methods=["GET"]
)
def get_multi_agent_mode():
    return jsonify({
        "enabled": mode_enabled(),
        "locked": mode_locked()
    }), 200


@multi_agent_bp.route(
    "/api/accommodations/multi-agent/mode",
    methods=["POST"]
)
def update_multi_agent_mode():

    if mode_locked():
        return jsonify({
            "error":
                "Multi-Agent is locked off by deployment configuration"
        }), 403

    data = request.get_json(silent=True) or {}

    enabled = data.get("enabled")

    if not isinstance(enabled, bool):
        return jsonify({
            "error":
                "enabled must be true or false"
        }), 400

    set_mode_enabled(enabled)

    return jsonify({
        "enabled": mode_enabled(),
        "locked": mode_locked()
    }), 200


# -----------------------------
# Health
# -----------------------------

@multi_agent_bp.route(
    "/api/accommodations/multi-agent/health",
    methods=["GET"]
)
def multi_agent_health():

    blocked = permitted()

    if blocked:
        return blocked

    try:
        result = check_multi_agent_health()

        return jsonify(result), 200

    except RequestException as exc:
        return fail(exc)


# -----------------------------
# Start workflow
# -----------------------------

@multi_agent_bp.route(
    "/api/accommodations/multi-agent/workflow",
    methods=["POST"]
)
def start_multi_agent_workflow():

    blocked = permitted()

    if blocked:
        return blocked

    data = request.get_json(silent=True) or {}

    user_request = (
        data.get("user_request") or ""
    ).strip()

    if not user_request:
        return jsonify({
            "error":
                "user_request is required"
        }), 400

    try:
        # Use real Accommodation DB records as evidence
        city, max_price = extract_accommodation_filters(user_request)
        print("MULTI-AGENT FILTER:", city, max_price)
        
        evidence = get_all_accommodations(city=city, max_price=max_price)
        print(
            "EVIDENCE:",
            [
                (
                    item["accommodation_name"],
                    item["city"],
                    item["price_per_night"]
                )
                for item in evidence
            ]
        )

        if not evidence:
            return jsonify({"error": "No accommodation evidence matched the request."}), 404

        result = run_multi_agent_workflow(
            feature="accommodation",
            user_request=user_request,
            evidence=evidence
        )

        return jsonify(result), 202

    except RequestException as exc:
        return fail(exc)


# -----------------------------
# Get workflow
# -----------------------------

@multi_agent_bp.route(
    "/api/accommodations/multi-agent/workflow/<workflow_id>",
    methods=["GET"]
)
def get_multi_agent_workflow(workflow_id):

    blocked = permitted()

    if blocked:
        return blocked

    try:
        result = get_workflow(
            workflow_id,
            feature="accommodation"
        )

        return jsonify(result), 200

    except RequestException as exc:
        return fail(exc)


# -----------------------------
# Human review
# -----------------------------

@multi_agent_bp.route(
    "/api/accommodations/multi-agent/review",
    methods=["POST"]
)
def review_multi_agent_workflow():

    blocked = permitted()

    if blocked:
        return blocked

    data = request.get_json(
        silent=True
    ) or {}

    workflow_id = (
        data.get("workflow_id") or ""
    ).strip()

    decision = (
        data.get("decision") or ""
    ).strip()

    correction = (
        data.get("correction") or ""
    ).strip()

    if not workflow_id:
        return jsonify({
            "error":
                "workflow_id is required"
        }), 400

    if decision not in (
        "Accept",
        "Partially Accept",
        "Reject"
    ):
        return jsonify({
            "error":
                "decision must be Accept, "
                "Partially Accept, or Reject"
        }), 400

    if (
        decision == "Partially Accept"
        and not correction
    ):
        return jsonify({
            "error":
                "correction is required "
                "for Partially Accept"
        }), 400

    try:
        result = submit_human_review(
            workflow_id=workflow_id,
            decision=decision,
            correction=correction
        )

        return jsonify(result), 200

    except RequestException as exc:
        return fail(exc)