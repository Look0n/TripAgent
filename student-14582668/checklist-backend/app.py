import os

from flask import Flask, jsonify
from flask_cors import CORS

from routes.ai_mode import ai_bp
from routes.normal_ui import normal_bp


def create_app():
    app = Flask(__name__)

    CORS(app)

    app.register_blueprint(normal_bp)
    app.register_blueprint(ai_bp)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "healthy",
            "service": "checklist-backend"
        }), 200

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("CHECKLIST_BACKEND_PORT", "5004")),
        debug=False
    )
