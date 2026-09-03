from flask import Flask
from flask_cors import CORS
import os

from routes.normal_ui import normal_bp
from routes.ai_mode import ai_bp

def create_app():
    app = Flask(__name__)

    CORS(app)

    app.register_blueprint(normal_bp)
    app.register_blueprint(ai_bp)

    return app


app = create_app()

@app.route("/health", methods=["GET"])
def health():
    return {
        "status": "ok",
        "service": "accommodation-backend"
    }, 200
    
if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5002,
        debug=True
    )
    