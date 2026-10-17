"""Authenticated Account proxy for shared multi-agent workflows.

Local demo: workflow IDs are not bound to individual customers.
Human review records a decision but never modifies saved preferences.
"""
import os
from flask import Blueprint, jsonify, request, current_app
from routes.normal_ui import login_required
from services.database_api import get_preferences
from services.multi_agent_client import call_server, MultiAgentClientError

multi_agent_bp = Blueprint("account_multi_agent", __name__)

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
    return jsonify({"error": str(exc)}), exc.status_code

@multi_agent_bp.get("/api/account/multi-agent/mode")
def mode():
    _, error = login_required()
    if error: return error
    return jsonify({"enabled": mode_enabled(), "locked": mode_locked()})

@multi_agent_bp.put("/api/account/multi-agent/mode")
def update_mode():
    _, error = login_required()
    if error: return error
    data = request.get_json(silent=True) or {}
    if not isinstance(data.get("enabled"), bool):
        return jsonify({"error": "enabled must be true or false"}), 400
    if mode_locked() and data["enabled"]:
        return jsonify({"error": "Multi-Agent is locked off by deployment configuration"}), 403
    return jsonify({"enabled": set_mode_enabled(data["enabled"]), "locked": mode_locked()})

@multi_agent_bp.post("/api/account/multi-agent/workflow")
def start():
    customer_id, error = login_required()
    if error: return error
    blocked = permitted()
    if blocked: return blocked
    data = request.get_json(silent=True) or {}
    text = data.get("user_request", "")
    if not isinstance(text, str) or not 1 <= len(text.strip()) <= 4000:
        return jsonify({"error": "user_request must be 1–4000 characters"}), 400
    try:
        response = get_preferences(customer_id)
        if response.status_code == 404:
            preferences = {}
        else:
            response.raise_for_status()
            preferences = response.json()
        # Minimise data sent to the LLM. Never send authentication fields.
        if isinstance(preferences, dict):
            preferences = {k: v for k, v in preferences.items()
                           if k.lower() not in ("customer_id", "password", "email", "phone", "first_name", "last_name")}
        else:
            preferences = {}
        if not preferences:
            return jsonify({"error": "Save your travel preferences before generating a personalised trip plan."}), 400
        result = call_server("POST", "/workflow", payload={
            "feature": "account", "user_request": text.strip(),
            "context": {"task": "account_auto_destination_trip_plan", "preferences": preferences, "constraints": {"destination_selection": "agent", "read_only": True, "bookings_allowed": False}}
        })
        workflow_id = result.get("workflow_id")
        if not isinstance(workflow_id, str) or not workflow_id:
            return jsonify({"error": "Multi-Agent server did not return a workflow ID"}), 502
        return jsonify(result), 202
    except MultiAgentClientError as exc:
        return fail(exc)
    except Exception:
        current_app.logger.exception("Account Multi-Agent workflow submission failed")
        return jsonify({"error": "Unable to create Account workflow"}), 503

@multi_agent_bp.get("/api/account/multi-agent/workflow/<workflow_id>")
def get_one(workflow_id):
    _, error = login_required()
    if error: return error
    blocked = permitted()
    if blocked: return blocked
    try:
        return jsonify(call_server("GET", f"/workflow/{workflow_id}", params={"feature": "account"}))
    except MultiAgentClientError as exc: return fail(exc)

@multi_agent_bp.post("/api/account/multi-agent/workflow/<workflow_id>/review")
def review(workflow_id):
    _, error = login_required()
    if error: return error
    blocked = permitted()
    if blocked: return blocked
    data = request.get_json(silent=True) or {}
    if data.get("decision") not in ("Accept", "Partially Accept", "Reject"):
        return jsonify({"error": "Invalid decision"}), 400
    correction = data.get("correction", "")
    if not isinstance(correction, str) or len(correction) > 4000:
        return jsonify({"error": "Invalid correction"}), 400
    try:
        return jsonify(call_server("POST", f"/workflow/{workflow_id}/review", payload={
            "feature": "account", "decision": data["decision"], "correction": correction
        }))
    except MultiAgentClientError as exc: return fail(exc)
