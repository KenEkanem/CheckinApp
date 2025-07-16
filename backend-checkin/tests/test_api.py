from datetime import datetime

import pytest

from app import create_app
from app.extensions import db
from app.models import Event, Guest


@pytest.fixture()
def client():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "CHECKIN_START_DATE": datetime(2000, 1, 1),
            "EVENT_CODE": "TEST2026",
        }
    )
    with app.app_context():
        db.create_all()
        db.session.add(Event(code="TEST2026", name="The Gathering 2026"))
        db.session.add(
            Guest(
                name="Ada Example",
                email="ada@example.com",
                unique_id="ABC123",
                group="Blue",
            )
        )
        db.session.commit()
        yield app.test_client()


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
