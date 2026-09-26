import traceback
import requests

from flask import Blueprint, jsonify, request

from services.rag_client import ask_rag


rag_bp = Blueprint(
    "rag",
    __name__,
)


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