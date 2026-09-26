from flask import Flask, jsonify, request
from rag_pipeline import answer_question, refresh_corpus, retrieve_context

app = Flask(__name__)

@app.get("/health")
def health():
    return jsonify({"status": "healthy", "service": "tripagent-rag"}), 200

@app.post("/rag/refresh")
def refresh():
    data = request.get_json(silent=True) or {}
    result = refresh_corpus(data.get("feature"), data.get("caller", "http"))
    return jsonify(result), 200 if result.get("status") == "success" else 400

@app.post("/rag/retrieve")
def retrieve():
    data = request.get_json(silent=True) or {}
    result = retrieve_context(data.get("query", ""), data.get("feature"),
                              data.get("k", 5), data.get("caller", "http"))
    return jsonify(result), 200 if result.get("status") == "success" else 400

@app.post("/rag/answer")
def answer():
    data = request.get_json(silent=True) or {}
    result = answer_question(data.get("query", ""), data.get("feature"),
                             data.get("k", 5), data.get("caller", "http"))
    return jsonify(result), 200 if result.get("status") == "success" else 400

if __name__ == "__main__":
    print("TripAgent Shared RAG HTTP Server: http://localhost:7002")
    app.run(host="0.0.0.0", port=7002, debug=False)
