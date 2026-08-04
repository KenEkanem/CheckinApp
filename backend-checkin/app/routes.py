import re
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import func, select, update
from sqlalchemy.exc import SQLAlchemyError

from .extensions import db
from .models import Event, Guest


api = Blueprint("api", __name__, url_prefix="/api")
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def error_response(message, status, code):
    return jsonify({"error": {"code": code, "message": message}}), status


def checkin_is_open():
    start = current_app.config["CHECKIN_START_DATE"]
    now = datetime.now(start.tzinfo) if start.tzinfo else datetime.now()
    return now >= start


def find_event(value):
    supplied = str(value or "").strip().upper()
    if not supplied:
        return None
    return db.session.execute(
        select(Event).where(func.upper(Event.code) == supplied, Event.active.is_(True))
    ).scalar_one_or_none()


@api.get("/health")
def health():
    return jsonify({"status": "ok", "service": "wegatherevents-api"})


@api.get("/config")
def public_config():
    start = current_app.config["CHECKIN_START_DATE"]
    return jsonify(
        {
            "checkinOpen": checkin_is_open(),
            "checkinStartsAt": start.isoformat(),
        }
    )


@api.post("/events/select")
def select_event():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("A JSON request body is required.", 400, "INVALID_BODY")
    try:
        event = find_event(payload.get("eventCode"))
    except SQLAlchemyError:
        current_app.logger.exception("Database error while selecting an event")
        return error_response(
            "The event service is temporarily unavailable.", 503, "DATABASE_UNAVAILABLE"
        )
    if event is None:
        return error_response(
            "We could not find an event with that code.", 404, "EVENT_NOT_FOUND"
        )

    details = event.to_dict()
    details["checkinOpen"] = checkin_is_open()
    return jsonify({"event": details})


@api.post("/check-ins")
def create_checkin():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("A JSON request body is required.", 400, "INVALID_BODY")

    email = str(payload.get("email", "")).strip().lower()
    unique_id = str(payload.get("uniqueId", "")).strip()
    method = str(payload.get("method", "email")).strip().lower()

    if not EMAIL_PATTERN.match(email):
        return error_response(
            "Enter a valid email address.", 422, "INVALID_EMAIL"
        )
    if method not in {"email", "barcode"}:
        return error_response(
            "Method must be either email or barcode.", 422, "INVALID_METHOD"
        )
    if method == "barcode" and not unique_id:
        return error_response(
            "A guest ID is required for barcode check-in.",
            422,
            "MISSING_UNIQUE_ID",
        )
    if not checkin_is_open():
        start = current_app.config["CHECKIN_START_DATE"]
        return (
            jsonify(
                {
                    "error": {
                        "code": "CHECKIN_NOT_OPEN",
                        "message": "Check-in is not open yet.",
                    },
                    "checkinStartsAt": start.isoformat(),
                }
            ),
            403,
        )

    filters = [func.lower(Guest.email) == email]
    if method == "barcode":
        filters.append(Guest.unique_id == unique_id)

    try:
        event = find_event(payload.get("eventCode"))
        if event is None:
            return error_response(
                "Select a valid event before checking in guests.",
                403,
                "INVALID_EVENT_CODE",
            )
        guest = db.session.execute(select(Guest).where(*filters)).scalar_one_or_none()
        if guest is None:
            return error_response(
                "We could not find a guest with those details.",
                404,
                "GUEST_NOT_FOUND",
            )

        if guest.time_checked_in is not None:
            return jsonify({"status": "already_checked_in", "guest": guest.to_dict()})

        # Only the first concurrent request can change a null check-in time.
        result = db.session.execute(
            update(Guest)
            .where(Guest.id == guest.id, Guest.time_checked_in.is_(None))
            .values(time_checked_in=func.now())
        )
        db.session.commit()
        db.session.refresh(guest)

        status = "checked_in" if result.rowcount == 1 else "already_checked_in"
        return jsonify({"status": status, "guest": guest.to_dict()})
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("Database error during check-in")
        return error_response(
            "The check-in service is temporarily unavailable.",
            503,
            "DATABASE_UNAVAILABLE",
        )
