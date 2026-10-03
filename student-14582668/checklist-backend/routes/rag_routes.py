from flask import Blueprint, jsonify, request

from services.rag_client import (
    RAGClientError,
    answer_question,
    check_rag_status,
    is_rag_enabled,
    refresh_checklist_corpus,
    retrieve_context,
)


rag_bp = Blueprint(
    "checklist_rag",
    __name__,
    url_prefix="/api/checklist-items/rag",
)


@rag_bp.get("/status")
def rag_status():
    try:
        return jsonify(check_rag_status()), 200

    except RAGClientError as exc:
        return jsonify({
            "enabled": is_rag_enabled(),
            "available": False,
            "error": str(exc),
        }), exc.status_code


@rag_bp.post("/refresh")
def rag_refresh():
    if not is_rag_enabled():
        return jsonify({
            "status": "error",
            "error": "RAG mode is disabled",
        }), 403

    try:
        return jsonify(refresh_checklist_corpus()), 200

    except RAGClientError as exc:
        return jsonify({
            "status": "error",
            "error": str(exc),
        }), exc.status_code


def handle_question(operation):
    if not is_rag_enabled():
        return jsonify({
            "status": "error",
            "error": "RAG mode is disabled",
        }), 403

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "error": "A JSON object is required",
        }), 400

    unknown_fields = set(data) - {"query", "k"}

    if unknown_fields:
        return jsonify({
            "status": "error",
            "error": "Unsupported request fields",
            "fields": sorted(unknown_fields),
        }), 400

    query = data.get("query")
    k = data.get("k", 5)

    if not isinstance(query, str) or not query.strip():
        return jsonify({
            "status": "error",
            "error": "query must be non-empty text",
        }), 400

    query = query.strip()

    if len(query) > 2000:
        return jsonify({
            "status": "error",
            "error": "query must not exceed 2000 characters",
        }), 400

    if type(k) is not int or not 1 <= k <= 20:
        return jsonify({
            "status": "error",
            "error": "k must be an integer between 1 and 20",
        }), 400

    try:
        return jsonify(operation(query, k)), 200

    except RAGClientError as exc:
        return jsonify({
            "status": "error",
            "error": str(exc),
        }), exc.status_code


@rag_bp.post("/retrieve")
def rag_retrieve():
    return handle_question(retrieve_context)


@rag_bp.post("/answer")
def rag_answer():
    return handle_question(answer_question)