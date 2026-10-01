from flask import Blueprint, jsonify, request

from services.rag_client import (
    RAGClientError,
    answer_question,
    check_rag_status,
    is_rag_enabled,
    refresh_flight_corpus,
    retrieve_context,
    set_rag_enabled,
)
from views.html_formatters import format_rag_answer


rag_bp = Blueprint(
    "rag",
    __name__
)


HTML_HEADERS = {"Content-Type": "text/html; charset=utf-8"}


@rag_bp.route("/api/flight/rag/mode", methods=["GET", "PUT"])
def rag_mode():
    if request.method == "GET":
        return jsonify({"enabled": is_rag_enabled()}), 200

    data = request.get_json(silent=True) or {}
    enabled = data.get("enabled")

    if not isinstance(enabled, bool):
        return jsonify({
            "error": "enabled must be true or false"
        }), 400

    return jsonify({"enabled": set_rag_enabled(enabled)}), 200


@rag_bp.route("/api/flight/rag/status", methods=["GET"])
def rag_status():
    return jsonify(check_rag_status()), 200


@rag_bp.route("/api/flight/rag/refresh", methods=["POST"])
def rag_refresh():
    try:
        return jsonify(refresh_flight_corpus()), 200
    except RAGClientError as exc:
        return jsonify({"error": str(exc)}), 503


@rag_bp.route("/api/flight/rag/retrieve", methods=["POST"])
def rag_retrieve():
    data = request.get_json(silent=True) or {}

    query = str(data.get("query", "")).strip()

    if not query:
        return jsonify({"error": "query is required"}), 400

    try:
        return jsonify(
            retrieve_context(query, data.get("k", 8))
        ), 200
    except RAGClientError as exc:
        return jsonify({"error": str(exc)}), 503


@rag_bp.route("/api/flight/rag/answer", methods=["POST"])
def rag_answer():
    data = request.get_json(silent=True) or {}

    query = str(data.get("query", "")).strip()

    if not query:
        return jsonify({"error": "query is required"}), 400

    try:
        return jsonify(
            answer_question(query, data.get("k", 8))
        ), 200
    except RAGClientError as exc:
        return jsonify({"error": str(exc)}), 503


@rag_bp.route("/api/flight/rag/answer/html", methods=["POST"])
def rag_answer_html():
    query = str(request.form.get("query", "")).strip()

    if not query:
        return (
            '<p class="warning">Enter a question about the flight '
            'service.</p>',
            400,
            HTML_HEADERS,
        )

    try:
        result = answer_question(query, request.form.get("k", 8))
    except RAGClientError as exc:
        return (
            f'<p class="warning">RAG unavailable: {exc}</p>',
            503,
            HTML_HEADERS,
        )

    return format_rag_answer(result), 200, HTML_HEADERS
