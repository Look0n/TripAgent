# Multi-Agent routes for the Attractions feature (Release 2).
# Frontend calls these, backend forwards to the shared Multi-Agent Server.
#
# The backend collects attraction records from the Attractions database and
# passes them to the Planner -> Worker -> Reviewer agents as context.evidence,
# so recommendations can only reference attractions that really exist.
# The human decision (Accept / Partially Accept / Reject) is recorded on the
# Multi-Agent Server; nothing is written to the attractions database.

import requests

from flask import Blueprint, jsonify, request

from services.database_api import get_all_attractions
from services.feature_flags import env_flag, multi_agent_locked
from services.multi_agent_client import (
    MultiAgentClientError,
    call_server,
    check_multi_agent_health,
)


multi_agent_bp = Blueprint("multi_agent", __name__)


FEATURE = "attractions"
MAX_REQUEST_CHARS = 4000
MAX_EVIDENCE_RECORDS = 15
DECISIONS = ("Accept", "Partially Accept", "Reject")

EVIDENCE_FIELDS = (
    "attraction_id",
    "name",
    "category",
    "city",
    "price",
    "average_rating",
    "description",
)


# Off at startup unless MULTI_AGENT_ENABLED=true; toggled from the frontend.
_state = {
    "enabled": env_flag("MULTI_AGENT_ENABLED", "false"),
}


def mode_enabled():
    return _state["enabled"] and not multi_agent_locked()


def blocked_response():
    if multi_agent_locked():
        return jsonify({
            "status": "error",
            "error": "Multi-Agent is locked off by deployment configuration.",
        }), 403

    if not _state["enabled"]:
        return jsonify({
            "status": "error",
            "error": "Multi-Agent Mode is disabled.",
        }), 403

    return None


def error_response(exc):
    return jsonify({
        "status": "error",
        "error": str(exc),
    }), exc.status_code


def clean_text(value, max_length=100):
    return str(value or "").strip()[:max_length]


def parse_max_price(value):
    if value in (None, ""):
        return None

    try:
        price = float(value)

    except (TypeError, ValueError) as exc:
        raise ValueError("max_price must be a number.") from exc

    if price < 0:
        raise ValueError("max_price must not be negative.")

    return price


# Collect candidate attractions the agents are allowed to reason over.
def build_evidence(city, category, max_price):
    records = get_all_attractions(
        city=city or None,
        category=category or None,
        max_price=max_price,
    )

    if not isinstance(records, list):
        return []

    evidence = []

    for record in records[:MAX_EVIDENCE_RECORDS]:
        if not isinstance(record, dict):
            continue

        evidence.append({
            field: record.get(field)
            for field in EVIDENCE_FIELDS
            if record.get(field) is not None
        })

    return evidence


# GET /api/attractions/multi-agent/mode - is Multi-Agent Mode on?
@multi_agent_bp.route(
    "/api/attractions/multi-agent/mode",
    methods=["GET"]
)
def get_mode():
    return jsonify({
        "enabled": mode_enabled(),
        "locked": multi_agent_locked(),
    }), 200


# PUT /api/attractions/multi-agent/mode - turn Multi-Agent Mode on/off.
@multi_agent_bp.route(
    "/api/attractions/multi-agent/mode",
    methods=["PUT"]
)
def set_mode():
    data = request.get_json(silent=True) or {}
    enabled = data.get("enabled")

    if not isinstance(enabled, bool):
        return jsonify({
            "status": "error",
            "error": "enabled must be true or false.",
        }), 400

    if enabled and multi_agent_locked():
        return jsonify({
            "status": "error",
            "error": "Multi-Agent is locked off by deployment configuration.",
        }), 403

    _state["enabled"] = enabled

    return jsonify({
        "enabled": mode_enabled(),
        "locked": multi_agent_locked(),
    }), 200


# GET /api/attractions/multi-agent/health - is the Multi-Agent Server up?
@multi_agent_bp.route(
    "/api/attractions/multi-agent/health",
    methods=["GET"]
)
def multi_agent_health():
    result = check_multi_agent_health()
    result["enabled"] = mode_enabled()
    result["locked"] = multi_agent_locked()

    status_code = 200 if result["status"] == "connected" else 503

    return jsonify(result), status_code


# POST /api/attractions/multi-agent/workflow - start Planner -> Worker -> Reviewer.
@multi_agent_bp.route(
    "/api/attractions/multi-agent/workflow",
    methods=["POST"]
)
def create_workflow():
    blocked = blocked_response()

    if blocked:
        return blocked

    data = request.get_json(silent=True) or {}

    user_request = clean_text(
        data.get("user_request"),
        MAX_REQUEST_CHARS,
    )

    if not user_request:
        return jsonify({
            "status": "error",
            "error": "user_request is required.",
        }), 400

    city = clean_text(data.get("city"))
    category = clean_text(data.get("category"))

    try:
        max_price = parse_max_price(data.get("max_price"))

    except ValueError as exc:
        return jsonify({
            "status": "error",
            "error": str(exc),
        }), 400

    try:
        evidence = build_evidence(city, category, max_price)

    except requests.RequestException:
        return jsonify({
            "status": "error",
            "error": "Attractions database is unavailable.",
        }), 503

    if not evidence:
        return jsonify({
            "status": "error",
            "error": (
                "No attractions match these filters, so there is no "
                "evidence for the agents to work from."
            ),
        }), 400

    try:
        result = call_server("POST", "/workflow", payload={
            "feature": FEATURE,
            "user_request": user_request,
            "context": {
                "task": "attraction_recommendation",
                "filters": {
                    "city": city or None,
                    "category": category or None,
                    "max_price": max_price,
                },
                "evidence": evidence,
                "constraints": {
                    "read_only": True,
                    "bookings_allowed": False,
                    "evidence_only": True,
                },
            },
        })

    except MultiAgentClientError as exc:
        return error_response(exc)

    if not isinstance(result.get("workflow_id"), str):
        return jsonify({
            "status": "error",
            "error": "Multi-Agent Server did not return a workflow ID.",
        }), 502

    result["evidence"] = evidence

    return jsonify(result), 202


# GET /api/attractions/multi-agent/workflow/<id> - poll workflow progress.
@multi_agent_bp.route(
    "/api/attractions/multi-agent/workflow/<workflow_id>",
    methods=["GET"]
)
def get_workflow(workflow_id):
    blocked = blocked_response()

    if blocked:
        return blocked

    try:
        result = call_server(
            "GET",
            f"/workflow/{workflow_id}",
            params={"feature": FEATURE},
        )

    except MultiAgentClientError as exc:
        return error_response(exc)

    return jsonify(result), 200


# POST /api/attractions/multi-agent/workflow/<id>/review - human decision.
@multi_agent_bp.route(
    "/api/attractions/multi-agent/workflow/<workflow_id>/review",
    methods=["POST"]
)
def review_workflow(workflow_id):
    blocked = blocked_response()

    if blocked:
        return blocked

    data = request.get_json(silent=True) or {}

    decision = data.get("decision")
    correction = data.get("correction", "")

    if decision not in DECISIONS:
        return jsonify({
            "status": "error",
            "error": "decision must be one of: " + ", ".join(DECISIONS),
        }), 400

    if not isinstance(correction, str) or len(correction) > MAX_REQUEST_CHARS:
        return jsonify({
            "status": "error",
            "error": "Invalid correction.",
        }), 400

    if decision == "Partially Accept" and not correction.strip():
        return jsonify({
            "status": "error",
            "error": "A correction is required for Partially Accept.",
        }), 400

    try:
        result = call_server(
            "POST",
            f"/workflow/{workflow_id}/review",
            payload={
                "feature": FEATURE,
                "decision": decision,
                "correction": correction,
            },
        )

    except MultiAgentClientError as exc:
        return error_response(exc)

    return jsonify(result), 200


# GET /api/attractions/multi-agent/history - recent attractions workflows.
@multi_agent_bp.route(
    "/api/attractions/multi-agent/history",
    methods=["GET"]
)
def history():
    blocked = blocked_response()

    if blocked:
        return blocked

    try:
        result = call_server(
            "GET",
            "/workflow/history",
            params={"feature": FEATURE},
        )

    except MultiAgentClientError as exc:
        return error_response(exc)

    return jsonify(result), 200
