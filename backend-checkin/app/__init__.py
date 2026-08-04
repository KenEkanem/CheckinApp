import os

from flask import Flask, jsonify

from .extensions import cors
from .routes import api


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        MANAGEMENT_API_URL=os.getenv(
            "MANAGEMENT_API_URL", "http://127.0.0.1:5004/api"
        ).rstrip("/"),
        CHECKIN_SERVICE_TOKEN=os.getenv(
            "CHECKIN_SERVICE_TOKEN", ""
        ),
        MANAGEMENT_API_TIMEOUT=float(os.getenv("MANAGEMENT_API_TIMEOUT", "10")),
    )
    if test_config:
        app.config.update(test_config)

    allowed_origins = os.getenv(
        "FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    cors.init_app(app, resources={r"/api/*": {"origins": allowed_origins}})
    app.register_blueprint(api)

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Route not found."}}), 404

    return app
