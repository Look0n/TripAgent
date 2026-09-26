from flask import Blueprint, jsonify, request
from routes.normal_ui import login_required
from services.rag_client import (
    RAGClientError, answer_question, check_rag_status, is_rag_enabled,
    refresh_account_corpus, retrieve_context, set_rag_enabled)

rag_bp = Blueprint("rag", __name__)

@rag_bp.get("/api/account/rag/mode")
def rag_mode():
    _, error = login_required()
    if error: return error
    return jsonify({"enabled": is_rag_enabled()}), 200

@rag_bp.put("/api/account/rag/mode")
def update_rag_mode():
    _, error = login_required()
    if error: return error
    data = request.get_json(silent=True) or {}
    if not isinstance(data.get("enabled"), bool):
        return jsonify({"error": "enabled must be true or false"}), 400
    return jsonify({"enabled": set_rag_enabled(data["enabled"])}), 200

@rag_bp.get("/api/account/rag/status")
def rag_status():
    _, error = login_required()
    if error: return error
    status = check_rag_status()
    return jsonify(status), 200 if (status.get("available") or not status.get("enabled")) else 503

@rag_bp.post("/api/account/rag/retrieve")
def rag_retrieve():
    _, error = login_required()
    if error: return error
    data = request.get_json(silent=True) or {}
    query = str(data.get("query", "")).strip()
    if not query: return jsonify({"error": "Query is required"}), 400
    try:
        return jsonify(retrieve_context(query, data.get("k", 5))), 200
    except RAGClientError as exc:
        return jsonify({"error": str(exc)}), 503

@rag_bp.post("/api/account/rag/answer")
def rag_answer():
    _, error = login_required()
    if error: return error
    data = request.get_json(silent=True) or {}
    query = str(data.get("query", "")).strip()
    if not query: return jsonify({"error": "Question is required"}), 400
    try:
        return jsonify(answer_question(query, data.get("k", 5))), 200
    except RAGClientError as exc:
        return jsonify({"error": str(exc)}), 503

@rag_bp.post("/api/account/rag/refresh")
def rag_refresh():
    _, error = login_required()
    if error: return error
    try:
        return jsonify(refresh_account_corpus()), 200
    except RAGClientError as exc:
        return jsonify({"error": str(exc)}), 503
