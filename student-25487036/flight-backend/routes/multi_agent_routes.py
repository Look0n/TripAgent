"""Flight proxy for the shared, non-containerised Multi-Agent Server.

The flight backend is the only client of the Multi-Agent Server. Evidence is
retrieved from the flight database service over HTTP and passed to the Planner,
Worker and Reviewer agents, so recommendations can only reference flights that
exist in the database.
"""
import os

from flask import Blueprint, current_app, jsonify, request

from services.database_api import list_flights
from services.multi_agent_client import (
    MultiAgentClientError,
    call_server,
    check_status,
)
from views.html_formatters import (
    format_multi_agent_history,
    format_multi_agent_workflow,
)

multi_agent_bp = Blueprint("flight_multi_agent", __name__)

FEATURE = "flight"
MAX_EVIDENCE_RECORDS = 20
MAX_REQUEST_CHARS = 4000
DECISIONS = ("Accept", "Partially Accept", "Reject")

EVIDENCE_FIELDS = (
    "flight_id",
    "airline",
    "origin",
    "destination",
    "departure_time",
    "arrival_time",
    "duration",
    "price",
    "seat_availability",
)

HTML_HEADERS = {"Content-Type": "text/html; charset=utf-8"}

_multi_agent_enabled = False


def mode_enabled():
    return _multi_agent_enabled


def set_mode_enabled(enabled):
    global _multi_agent_enabled
    _multi_agent_enabled = bool(enabled)
    return _multi_agent_enabled


def mode_locked():
    return os.getenv("MULTI_AGENT_LOCKED", "false").lower() in (
        "true",
        "1",
        "yes",
        "on",
    )


def permitted():
    if mode_locked():
        return jsonify({
            "error": "Multi-Agent is locked off by deployment configuration"
        }), 403

    if not mode_enabled():
        return jsonify({"error": "Multi-Agent mode is OFF"}), 403

    return None


def fail(exc):
    return jsonify({"error": str(exc)}), exc.status_code


def clean_code(value):
    return str(value or "").strip().upper()


def build_evidence(origin, destination):
    """Retrieve candidate flights the agents are permitted to reason over."""
    response = list_flights(origin or None, destination or None)
    response.raise_for_status()

    records = response.json()

    if isinstance(records, dict):
        records = records.get("flights", [])

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


def validate_request_text(text):
    if not isinstance(text, str):
        return None
    text = text.strip()
    if not 1 <= len(text) <= MAX_REQUEST_CHARS:
        return None
    return text


def start_workflow(text, origin, destination):
    evidence = build_evidence(origin, destination)

    if not evidence:
        raise MultiAgentClientError(
            "No flight records match that route, so there is no evidence "
            "for the agents to work from.",
            400,
        )

    return call_server("POST", "/workflow", payload={
        "feature": FEATURE,
        "user_request": text,
        "context": {
            "task": "flight_itinerary_recommendation",
            "evidence": evidence,
            "constraints": {
                "read_only": True,
                "bookings_allowed": False,
                "evidence_only": True,
            },
        },
    })


@multi_agent_bp.get("/api/flight/multi-agent/mode")
def mode():
    return jsonify({"enabled": mode_enabled(), "locked": mode_locked()})


@multi_agent_bp.put("/api/flight/multi-agent/mode")
def update_mode():
    data = request.get_json(silent=True) or {}

    if not isinstance(data.get("enabled"), bool):
        return jsonify({"error": "enabled must be true or false"}), 400

    if mode_locked() and data["enabled"]:
        return jsonify({
            "error": "Multi-Agent is locked off by deployment configuration"
        }), 403

    return jsonify({
        "enabled": set_mode_enabled(data["enabled"]),
        "locked": mode_locked(),
    })


def render_mode_control():
    """HTML for the Multi-Agent mode switch shown in the flight frontend."""
    if mode_locked():
        return (
            '<p class="warning">Multi-Agent mode is <strong>locked off</strong>'
            ' by deployment configuration and cannot be enabled here.</p>'
        )

    enabled = mode_enabled()
    state = "ON" if enabled else "OFF"
    requested = "false" if enabled else "true"
    label = "Turn Multi-Agent off" if enabled else "Turn Multi-Agent on"

    return (
        f'<p>Multi-Agent mode is <strong>{state}</strong>. It starts off on'
        ' every backend restart as a deployment control.</p>'
        '<button type="button" class="primary-button"'
        ' hx-post="/api/flight/multi-agent/mode/html"'
        f" hx-vals='{{\"enabled\": \"{requested}\"}}'"
        ' hx-target="#multi-agent-mode"'
        f' hx-swap="innerHTML">{label}</button>'
    )


@multi_agent_bp.get("/api/flight/multi-agent/mode/html")
def mode_html():
    return render_mode_control(), 200, HTML_HEADERS


@multi_agent_bp.post("/api/flight/multi-agent/mode/html")
def update_mode_html():
    requested = request.form.get("enabled", "").lower() in (
        "true",
        "1",
        "yes",
        "on",
    )

    if not (mode_locked() and requested):
        set_mode_enabled(requested)

    return render_mode_control(), 200, HTML_HEADERS


@multi_agent_bp.get("/api/flight/multi-agent/status")
def status():
    result = check_status()
    result["enabled"] = mode_enabled()
    result["locked"] = mode_locked()
    return jsonify(result)


@multi_agent_bp.post("/api/flight/multi-agent/workflow")
def create_workflow():
    blocked = permitted()
    if blocked:
        return blocked

    data = request.get_json(silent=True) or {}
    text = validate_request_text(data.get("user_request"))

    if text is None:
        return jsonify({
            "error": f"user_request must be 1-{MAX_REQUEST_CHARS} characters"
        }), 400

    try:
        result = start_workflow(
            text,
            clean_code(data.get("origin")),
            clean_code(data.get("destination")),
        )
    except MultiAgentClientError as exc:
        return fail(exc)
    except Exception:
        current_app.logger.exception("Flight Multi-Agent submission failed")
        return jsonify({"error": "Unable to create flight workflow"}), 503

    if not isinstance(result.get("workflow_id"), str):
        return jsonify({
            "error": "Multi-Agent server did not return a workflow ID"
        }), 502

    return jsonify(result), 202


@multi_agent_bp.get("/api/flight/multi-agent/workflow/<workflow_id>")
def get_workflow(workflow_id):
    blocked = permitted()
    if blocked:
        return blocked

    try:
        return jsonify(call_server(
            "GET",
            f"/workflow/{workflow_id}",
            params={"feature": FEATURE},
        ))
    except MultiAgentClientError as exc:
        return fail(exc)


@multi_agent_bp.post("/api/flight/multi-agent/workflow/<workflow_id>/review")
def review_workflow(workflow_id):
    blocked = permitted()
    if blocked:
        return blocked

    data = request.get_json(silent=True) or {}
    decision = data.get("decision")

    if decision not in DECISIONS:
        return jsonify({
            "error": "decision must be one of: " + ", ".join(DECISIONS)
        }), 400

    correction = data.get("correction", "")

    if not isinstance(correction, str) or len(correction) > MAX_REQUEST_CHARS:
        return jsonify({"error": "Invalid correction"}), 400

    if decision == "Partially Accept" and not correction.strip():
        return jsonify({
            "error": "A correction is required when partially accepting"
        }), 400

    try:
        return jsonify(call_server(
            "POST",
            f"/workflow/{workflow_id}/review",
            payload={
                "feature": FEATURE,
                "decision": decision,
                "correction": correction,
            },
        ))
    except MultiAgentClientError as exc:
        return fail(exc)


@multi_agent_bp.get("/api/flight/multi-agent/history")
def history():
    blocked = permitted()
    if blocked:
        return blocked

    try:
        return jsonify(call_server(
            "GET",
            "/workflow/history",
            params={"feature": FEATURE},
        ))
    except MultiAgentClientError as exc:
        return fail(exc)


@multi_agent_bp.post("/api/flight/multi-agent/workflow/html")
def create_workflow_html():
    if mode_locked():
        return (
            '<p class="warning">Multi-Agent is locked off by deployment '
            'configuration.</p>',
            403,
            HTML_HEADERS,
        )

    if not mode_enabled():
        return (
            '<p class="warning">Multi-Agent mode is OFF. Turn it on to run '
            'the Planner, Worker and Reviewer workflow.</p>',
            403,
            HTML_HEADERS,
        )

    text = validate_request_text(request.form.get("user_request"))

    if text is None:
        return (
            '<p class="warning">Describe the flight you need before starting '
            'a workflow.</p>',
            400,
            HTML_HEADERS,
        )

    try:
        result = start_workflow(
            text,
            clean_code(request.form.get("origin")),
            clean_code(request.form.get("destination")),
        )
    except MultiAgentClientError as exc:
        return (
            f'<p class="warning">{exc}</p>',
            exc.status_code,
            HTML_HEADERS,
        )
    except Exception:
        current_app.logger.exception("Flight Multi-Agent submission failed")
        return (
            '<p class="warning">Unable to create the flight workflow.</p>',
            503,
            HTML_HEADERS,
        )

    return format_multi_agent_workflow(result), 202, HTML_HEADERS


@multi_agent_bp.get("/api/flight/multi-agent/workflow/<workflow_id>/html")
def get_workflow_html(workflow_id):
    try:
        result = call_server(
            "GET",
            f"/workflow/{workflow_id}",
            params={"feature": FEATURE},
        )
    except MultiAgentClientError as exc:
        return (
            f'<p class="warning">{exc}</p>',
            exc.status_code,
            HTML_HEADERS,
        )

    return format_multi_agent_workflow(result), 200, HTML_HEADERS


@multi_agent_bp.post("/api/flight/multi-agent/workflow/<workflow_id>/review/html")
def review_workflow_html(workflow_id):
    decision = request.form.get("decision")

    if decision not in DECISIONS:
        return (
            '<p class="warning">Select Accept, Partially Accept or '
            'Reject.</p>',
            400,
            HTML_HEADERS,
        )

    correction = request.form.get("correction", "")[:MAX_REQUEST_CHARS]

    if decision == "Partially Accept" and not correction.strip():
        return (
            '<p class="warning">A correction is required when partially '
            'accepting the reviewed result.</p>',
            400,
            HTML_HEADERS,
        )

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
        return (
            f'<p class="warning">{exc}</p>',
            exc.status_code,
            HTML_HEADERS,
        )

    return format_multi_agent_workflow(result), 200, HTML_HEADERS


@multi_agent_bp.get("/api/flight/multi-agent/history/html")
def history_html():
    try:
        result = call_server(
            "GET",
            "/workflow/history",
            params={"feature": FEATURE},
        )
    except MultiAgentClientError as exc:
        return (
            f'<p class="warning">{exc}</p>',
            exc.status_code,
            HTML_HEADERS,
        )

    return format_multi_agent_history(result), 200, HTML_HEADERS
