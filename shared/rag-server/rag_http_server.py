from flask import Flask, jsonify, request
from rag_pipeline import answer_question, refresh_corpus, retrieve_context

app = Flask(__name__)


def _json_body():
    data = request.get_json(silent=True)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")
    return data


def _positive_k(value, default=5):
    if value is None:
        return default
    if isinstance(value, bool):
        raise ValueError("k must be a positive integer.")
    try:
        value = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("k must be a positive integer.") from exc
    if value < 1 or value > 20:
        raise ValueError("k must be between 1 and 20.")
    return value


def _error_response(exc, status=400):
    return jsonify({"status": "error", "error": str(exc)}), status


@app.get("/health")
def health():
    return jsonify({"status": "healthy", "service": "tripagent-rag"}), 200


@app.post("/rag/refresh")
def refresh():
    try:
        data = _json_body()
        result = refresh_corpus(data.get("feature"), data.get("caller", "http"))
        return jsonify(result), 200 if result.get("status") == "success" else 400
    except ValueError as exc:
        return _error_response(exc)
    except Exception as exc:
        return _error_response(exc, 500)


@app.post("/rag/retrieve")
def retrieve():
    try:
        data = _json_body()
        query = str(data.get("query", "")).strip()
        if not query:
            raise ValueError("Query is required.")
        result = retrieve_context(query, data.get("feature"), _positive_k(data.get("k")), data.get("caller", "http"))
        return jsonify(result), 200 if result.get("status") == "success" else 400
    except ValueError as exc:
        return _error_response(exc)
    except Exception as exc:
        return _error_response(exc, 500)


@app.post("/rag/answer")
def answer():
    try:
        data = _json_body()
        query = str(data.get("query", "")).strip()
        if not query:
            raise ValueError("Question is required.")
        result = answer_question(query, data.get("feature"), _positive_k(data.get("k")), data.get("caller", "http"))
        return jsonify(result), 200 if result.get("status") == "success" else 400
    except ValueError as exc:
        return _error_response(exc)
    except Exception as exc:
        return _error_response(exc, 500)


if __name__ == "__main__":
    print("TripAgent Shared RAG HTTP Server: http://localhost:7002")
    app.run(host="0.0.0.0", port=7002, debug=False)
