from flask import Flask
from flask_cors import CORS

from routes.normal_ui import normal_bp
from routes.ai_mode import ai_bp
from routes.mcp_mode import mcp_bp
from routes.rag_mode import rag_bp
from routes.multi_agent_routes import multi_agent_bp, mode_enabled
from services.feature_flags import service_modes


def create_app():
    app = Flask(__name__)

    CORS(app)

    app.register_blueprint(normal_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(mcp_bp)
    app.register_blueprint(rag_bp)
    app.register_blueprint(multi_agent_bp)

    return app


app = create_app()


@app.route("/health", methods=["GET"])
def health():
    return {
        "status": "ok",
        "service": "attractions-backend"
    }, 200


# GET /api/attractions/modes - which AI services are enabled right now.
# Used by the frontend and by CI to confirm the cloud/CI baseline.
@app.route("/api/attractions/modes", methods=["GET"])
def modes():
    return service_modes(mode_enabled()), 200


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",  # noqa: S104 - required for Docker networking
        port=5003,
        debug=False
    )
