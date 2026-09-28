import traceback
import requests

from flask import Blueprint, jsonify, request

from services.rag_client import (
    check_rag_health,
    ask_rag,
    retrieve_rag,
    refresh_rag,
)


rag_bp = Blueprint(
    "rag",
    __name__,
)


@rag_bp.route(
    "/api/accommodations/rag/health",
    methods=["GET"]
)
def rag_health():

    try:
        check_rag_health()

        return jsonify({
            "status": "connected"
        }), 200

    except requests.RequestException:
        return jsonify({
            "status": "error",
            "error": "RAG server unavailable."
        }), 503
        

@rag_bp.route(
    "/api/accommodations/rag",
    methods=["POST"],
)
def accommodation_rag():
    data = request.get_json(silent=True) or {}

    question = str(
        data.get("question", "")
    ).strip()

    if not question:
        return jsonify({
            "status": "error",
            "error": "Question is required.",
        }), 400

    try:
        result = ask_rag(
            question=question,
            k=5,
        )

        if result.get("status") != "success":
            return jsonify({
                "status": "error",
                "result": result,
            }), 502

        return jsonify({
            "status": "success",
            "result": result,
        }), 200

    except requests.RequestException as exc:
        traceback.print_exc()

        return jsonify({
            "status": "error",
            "error": "RAG service unavailable.",
            "details": str(exc),
        }), 503

    except Exception as exc:
        traceback.print_exc()

        return jsonify({
            "status": "error",
            "error": "RAG request failed.",
            "details": str(exc),
        }), 500
        
        
@rag_bp.route(
    "/api/accommodations/rag/retrieve",
    methods=["POST"]
)
def retrieve_context():

    data = request.get_json(
        silent=True
    ) or {}

    question = str(
        data.get("question", "")
    ).strip()

    k = data.get("k", 5)

    if not question:
        return jsonify({
            "status": "error",
            "error": "Question is required."
        }), 400

    try:

        result = retrieve_rag(
            question=question,
            k=k,
        )

        return jsonify({
            "status": "success",
            "result": result,
        }), 200

    except Exception as error:

        return jsonify({
            "status": "error",
            "error": str(error),
        }), 503
        
        
@rag_bp.route(
    "/api/accommodations/rag/refresh",
    methods=["POST"]
)
def refresh_context():

    try:

        result = refresh_rag()

        return jsonify({
            "status": "success",
            "result": result,
        }), 200

    except Exception as error:

        return jsonify({
            "status": "error",
            "error": str(error),
        }), 503