import json
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import current_app

from .extensions import db
from .models import Event, Guest


class ManagementSyncError(RuntimeError):
    pass


def _get_json(path, query=None):
    base_url = current_app.config["GUEST_MANAGEMENT_API_URL"].rstrip("/")
    if not base_url:
        return None
    url = f"{base_url}/{path.lstrip('/')}"
    if query:
        url = f"{url}?{urlencode(query)}"
    try:
        request = Request(url, headers={"Accept": "application/json"})
        with urlopen(request, timeout=current_app.config["SYNC_TIMEOUT_SECONDS"]) as response:
            return json.load(response)
    except (HTTPError, URLError, TimeoutError, ValueError) as error:
        raise ManagementSyncError(f"Could not synchronize from {url}: {error}") from error


def notify_management_checkin(guest, event):
    """Notify Guest Management after a successful local check-in."""
    base_url = current_app.config["GUEST_MANAGEMENT_API_URL"].rstrip("/")
    if not base_url:
        return
    payload = json.dumps({
        "uniqueId": guest.unique_id,
        "email": guest.email,
        "eventCode": event.code,
        "checkedInAt": guest.time_checked_in.isoformat() if guest.time_checked_in else None,
    }).encode("utf-8")
    request = Request(
        f"{base_url}/check-ins/notify",
        data=payload,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=current_app.config["SYNC_TIMEOUT_SECONDS"]) as response:
            return json.load(response)
    except (HTTPError, URLError, TimeoutError) as error:
        raise ManagementSyncError(f"Could not notify {request.full_url}: {error}") from error


def _parse_datetime(value):
    if not value:
        return None
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def sync_event_from_management(event_code):
    """Upsert one event and its guest directory from Guest Management Studio."""
    code = str(event_code or "").strip().upper()
    if not code or not current_app.config["GUEST_MANAGEMENT_API_URL"]:
        return {"events": 0, "guests": 0}

    events = (_get_json("events") or {}).get("events", [])
    source_event = next(
        (event for event in events if str(event.get("code", "")).upper() == code and event.get("active", True)),
        None,
    )
    if source_event is None:
        return {"events": 0, "guests": 0}

    event = db.session.execute(
        db.select(Event).where(db.func.upper(Event.code) == code)
    ).scalar_one_or_none()
    if event is None:
        event = Event(code=code, name=source_event["name"])
        db.session.add(event)
    event.name = source_event["name"]
    event.starts_at = _parse_datetime(source_event.get("startsAt"))
    event.venue = source_event.get("venue")
    event.doors_open = source_event.get("doorsOpen")
    event.active = source_event.get("active", True)

    guests = (_get_json("guests", {"eventId": source_event["id"]}) or {}).get("guests", [])
    synced = 0
    for source in guests:
        email = str(source.get("email", "")).strip().lower()
        unique_id = str(source.get("uniqueId", "")).strip()
        name = str(source.get("name", "")).strip()
        if not email or not unique_id or not name:
            continue

        guest = db.session.execute(
            db.select(Guest).where(Guest.unique_id == unique_id)
        ).scalar_one_or_none()
        if guest is None:
            guest = db.session.execute(
                db.select(Guest).where(db.func.lower(Guest.email) == email)
            ).scalar_one_or_none()
        if guest is None:
            guest = Guest(name=name, email=email, unique_id=unique_id)
            db.session.add(guest)

        guest.name = name
        guest.email = email
        guest.unique_id = unique_id
        guest.group = source.get("tier") or source.get("classification") or source.get("group")
        source_checkin = _parse_datetime(source.get("checkedInAt"))
        if source_checkin is not None:
            guest.time_checked_in = source_checkin
        synced += 1

    db.session.commit()
    return {"events": 1, "guests": synced}
