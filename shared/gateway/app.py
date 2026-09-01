from flask import Flask

from routes.access_api import access_bp
from routes.gateway_routes import gateway_bp


def create_app():
    app = Flask(__name__)

    # Register shared authentication/session routes
    app.register_blueprint(access_bp)

    # Register protected service gateway routes
    app.register_blueprint(gateway_bp)

    @app.route("/health", methods=["GET"])
    def health():
        return {
            "service": "shared-gateway",
            "status": "healthy"
        }, 200

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )