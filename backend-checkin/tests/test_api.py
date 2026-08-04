import pytest

from app import create_app
from app.management_api import ManagementApiError


@pytest.fixture()
def client(monkeypatch):
    checked_in = False

    def fake_post(path, payload):
        nonlocal checked_in
        if path == "checkin/events/select":
            if str(payload.get("eventCode", "")).upper() != "TEST2026":
                raise ManagementApiError(
                    {"error": {"code": "EVENT_NOT_FOUND", "message": "We could not find an event with that code."}},
                    404,
                )
            return {
                "event": {
                    "name": "The Gathering 2026",
                    "code": "TEST2026",
                    "checkinOpen": True,
                    "startsAt": None,
                    "venue": None,
                    "doorsOpen": None,
                }
            }, 200

        if payload.get("uniqueId") == "WRONG":
            raise ManagementApiError(
                {"error": {"code": "GUEST_NOT_FOUND", "message": "We could not find a guest with those details."}},
                404,
            )
        status = "already_checked_in" if checked_in else "checked_in"
        checked_in = True
        return {
            "status": status,
            "displayFields": ["name", "email", "uniqueId", "tier", "checkedInAt"],
            "guest": {
                "name": "Ada Example",
                "email": "ada@example.com",
                "uniqueId": "ABC123",
                "group": "Blue",
                "checkedInAt": "2026-08-04T10:00:00+01:00",
            },
        }, 200

    monkeypatch.setattr("app.management_api.post", fake_post)
    app = create_app({"TESTING": True})
    return app.test_client()


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json["status"] == "ok"


def test_checkin_is_idempotent(client):
    payload = {"email": "ADA@example.com", "method": "email", "eventCode": "TEST2026"}
    first = client.post("/api/check-ins", json=payload)
    second = client.post("/api/check-ins", json=payload)
    assert first.status_code == 200
    assert first.json["status"] == "checked_in"
    assert "name" in first.json["displayFields"]
    assert first.json["guest"]["checkedInAt"] is not None
    assert second.json["status"] == "already_checked_in"


def test_barcode_requires_matching_id(client):
    response = client.post(
        "/api/check-ins",
        json={"email": "ada@example.com", "uniqueId": "WRONG", "method": "barcode", "eventCode": "TEST2026"},
    )
    assert response.status_code == 404
    assert response.json["error"]["code"] == "GUEST_NOT_FOUND"


def test_rejects_invalid_email(client):
    response = client.post(
        "/api/check-ins", json={"email": "not-an-email", "method": "email", "eventCode": "TEST2026"}
    )
    assert response.status_code == 422


def test_select_event(client):
    selected = client.post("/api/events/select", json={"eventCode": "test2026"})
    missing = client.post("/api/events/select", json={"eventCode": "wrong"})
    assert selected.status_code == 200
    assert selected.json["event"]["name"] == "The Gathering 2026"
    assert missing.status_code == 404


def test_management_service_failure_is_relayed(client, monkeypatch):
    def unavailable(_path, _payload):
        raise ManagementApiError(
            {"error": {"code": "MANAGEMENT_API_UNAVAILABLE", "message": "The management service is temporarily unavailable."}},
            503,
        )

    monkeypatch.setattr("app.management_api.post", unavailable)
    response = client.post("/api/events/select", json={"eventCode": "TEST2026"})
    assert response.status_code == 503
    assert response.json["error"]["code"] == "MANAGEMENT_API_UNAVAILABLE"
