from flask import Blueprint, jsonify, request

from services.checklist_context import (ChecklistContextError, build_checklist_context,)
from services.multi_agent_client import (MultiAgentClientError, call_server, is_multi_agent_enabled,)

multi_agent_bp = Blueprint("checklist_multi_agent", __name__, url_prefix="/api/checklist-items/multi-agent",)

WORKFLOW_STATUSES = {
    "queued",
    "running",
    "pending_review",
    "completed",
    "rejected",
    "failed"
}

VALID_DECISIONS = {
    "Accept",
    "Partially Accept",
    "Reject"
}

@multi_agent_bp.errorhandler(MultiAgentClientError)
@multi_agent_bp.errorhandler(ChecklistContextError)
def handle_service_error(exc):
    return jsonify({
        "error": str(exc)
    }), exc.status_code

@multi_agent_bp.before_request
def require_enabled_mode():
    if request.endpoint == "checklist_multi_agent.status":
        return None

    if not is_multi_agent_enabled():
        return jsonify({
            "error": "Multi-Agent mode is disabled",
        }), 403

    return None

def validate_workflow(result, expected_id=None):
    workflow_id = result.get("workflow_id")

    if(not isinstance(workflow_id, str) or not workflow_id or result.get("feature") != "checklist" or result.get("status") not in WORKFLOW_STATUSES or (expected_id is not None and workflow_id != expected_id)):
        raise MultiAgentClientError("Multi-Agent server returned an invalid workflow", 502)

    return result

@multi_agent_bp.get("/status")
def status():
    if not is_multi_agent_enabled():
        return jsonify({
            "enabled": False,
            "available": False,
        }), 200

    try:
        result = call_server("GET", "/health")

        if (
            result.get("service") != "multi-agent-server"
            or result.get("status") != "running"
            or "checklist" not in result.get("features", [])
        ):
            raise MultiAgentClientError(
                "Invalid Multi-Agent health response",
                502,
            )

        return jsonify({
            "enabled": True,
            "available": True,
        }), 200

    except MultiAgentClientError as exc:
        return jsonify({
            "enabled": True,
            "available": False,
            "error": str(exc),
        }), exc.status_code


@multi_agent_bp.post("/workflow")
def start_workflow():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "A JSON object is required",
        }), 400

    user_request = data.get("user_request")

    if (
        not isinstance(user_request, str)
        or not 1 <= len(user_request.strip()) <= 4000
    ):
        return jsonify({
            "error": "user_request must be 1-4000 characters",
        }), 400

    context = build_checklist_context()

    result = call_server(
        "POST",
        "/workflow",
        payload={
            "feature": "checklist",
            "user_request": user_request.strip(),
            "context": context,
        },
    )

    return jsonify(validate_workflow(result)), 202


@multi_agent_bp.get("/workflow/<uuid:workflow_id>")
def get_workflow(workflow_id):
    workflow_id = str(workflow_id)

    result = call_server(
        "GET",
        f"/workflow/{workflow_id}",
        params={"feature": "checklist"},
    )

    return jsonify(
        validate_workflow(result, workflow_id)
    ), 200


@multi_agent_bp.post("/workflow/<uuid:workflow_id>/review")
def review_workflow(workflow_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "A JSON object is required",
        }), 400

    decision = data.get("decision")
    correction = data.get("correction", "")

    if (
        not isinstance(decision, str)
        or decision not in VALID_DECISIONS
    ):
        return jsonify({
            "error": "Invalid decision",
        }), 400

    if not isinstance(correction, str) or len(correction) > 4000:
        return jsonify({
            "error": "correction must be text up to 4000 characters",
        }), 400

    if decision == "Partially Accept" and not correction.strip():
        return jsonify({
            "error": "Correction is required for partial acceptance",
        }), 400

    workflow_id = str(workflow_id)

    result = call_server(
        "POST",
        f"/workflow/{workflow_id}/review",
        payload={
            "feature": "checklist",
            "decision": decision,
            "correction": correction.strip(),
        },
    )

    return jsonify(
        validate_workflow(result, workflow_id)
    ), 200