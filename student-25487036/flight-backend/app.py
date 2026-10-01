import os

from flask import Flask, jsonify

from routes.normal_ui import normal_ui_bp
from routes.ai_mode import ai_mode_bp



def create_app():
    app = Flask(__name__)

    app.register_blueprint(normal_ui_bp)
    app.register_blueprint(ai_mode_bp)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "healthy",
            "service": "flight-backend"
        }), 200

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=False)