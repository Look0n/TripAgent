import os

from flask import Flask, jsonify

from routes.ai_mode import ai_mode_bp
from routes.normal_ui import normal_ui_bp
from routes.mcp_routes import mcp_bp
from routes.rag_routes import rag_bp


def create_app():
    app = Flask(__name__)

    app.secret_key = os.getenv(
        "SECRET_KEY",
        "tripagent-development-secret"
    )

    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax"
    )

    app.register_blueprint(
        normal_ui_bp
    )

    app.register_blueprint(
        ai_mode_bp
    )

    app.register_blueprint(
        mcp_bp
    )

    app.register_blueprint(
        rag_bp
    )

    @app.route(
        "/health",
        methods=["GET"]
    )
    def health():
        return jsonify({
            "status": "healthy",
            "service": "account-backend"
        }), 200

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5001,
        debug=False
    )