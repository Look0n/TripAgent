import os

from flask import Flask

from backend.routes import (
    ai_api_bp,
    auth_api_bp,
    normal_ui_bp,
    preference_api_bp,
    profile_api_bp,
)
from database.db import init_db


def create_app(testing=False):
    app = Flask(
        __name__,
        template_folder="frontend/templates",
        static_folder="frontend/static",
    )

    app.config["TESTING"] = testing
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-me")

    app.register_blueprint(normal_ui_bp)
    app.register_blueprint(auth_api_bp)
    app.register_blueprint(profile_api_bp)
    app.register_blueprint(preference_api_bp)
    app.register_blueprint(ai_api_bp)

    with app.app_context():
        init_db()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
