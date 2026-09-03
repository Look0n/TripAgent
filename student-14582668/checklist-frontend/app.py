import os

from flask import Flask, jsonify, render_template


def create_app():
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates"
    )

    @app.route("/", methods=["GET"])
    def checklist_page():
        api_url = os.getenv(
            "CHECKLIST_API_URL",
            "/api/checklist-items"
        ).rstrip("/")

        return render_template(
            "checklist.html",
            api_url=api_url
        )

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "healthy",
            "service": "checklist-frontend"
        }), 200

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("CHECKLIST_FRONTEND_PORT", "3004")),
        debug=False,
        use_reloader=False
    )
