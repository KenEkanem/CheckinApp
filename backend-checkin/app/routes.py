import re

from flask import Blueprint, jsonify, request

from . import management_api


api = Blueprint("api", __name__, url_prefix="/api")
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def error_response(message, status, code):
    return jsonify({"error": {"code": code, "message": message}}), status


def relay(path, payload):
    try:
        body, status = management_api.post(path, payload)
        return jsonify(body), status
    except management_api.ManagementApiError as exc:
        return jsonify(exc.body), exc.status


@api.get("/health")
def health():
    return jsonify({"status": "ok", "service": "wegatherevents-api"})


@api.get("/config")
def public_config():
    return jsonify({"checkinOpen": True, "checkinStartsAt": None})


@api.post("/events/select")
def select_event():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("A JSON request body is required.", 400, "INVALID_BODY")
    return relay("checkin/events/select", {"eventCode": payload.get("eventCode")})


@api.post("/check-ins")
def create_checkin():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("A JSON request body is required.", 400, "INVALID_BODY")

    email = str(payload.get("email", "")).strip().lower()
    method = str(payload.get("method", "email")).strip().lower()
    unique_id = str(payload.get("uniqueId", "")).strip()
    if not EMAIL_PATTERN.match(email):
        return error_response("Enter a valid email address.", 422, "INVALID_EMAIL")
    if method not in {"email", "barcode"}:
        return error_response("Method must be either email or barcode.", 422, "INVALID_METHOD")
    if method == "barcode" and not unique_id:
        return error_response("A guest ID is required for barcode check-in.", 422, "MISSING_UNIQUE_ID")

    return relay(
        "checkin/check-ins",
        {
            "email": email,
            "method": method,
            "uniqueId": unique_id,
            "eventCode": payload.get("eventCode"),
        },
    )
