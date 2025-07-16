import csv
import hashlib
import os
from datetime import datetime

import click
from flask import Flask, jsonify

from .extensions import cors, db
from .models import Event, Guest
from .routes import api


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://postgres:postgres@localhost:5432/checkin_app",
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        CHECKIN_START_DATE=datetime.fromisoformat(
            os.getenv("CHECKIN_START_DATE", "2024-09-11T09:00:00+01:00")
        ),
        EVENT_NAME=os.getenv("EVENT_NAME", "The Gathering 2026"),
        EVENT_CODE=os.getenv("EVENT_CODE", "GATHER2026"),
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    allowed_origins = os.getenv("FRONTEND_ORIGINS", "http://localhost:5173").split(",")
    cors.init_app(app, resources={r"/api/*": {"origins": allowed_origins}})
    app.register_blueprint(api)

    @app.cli.command("init-db")
    def init_db_command():
        """Create missing database tables without deleting existing data."""
        db.create_all()
        configured_code = app.config["EVENT_CODE"].strip().upper()
        existing_event = db.session.execute(
            db.select(Event).where(db.func.upper(Event.code) == configured_code)
        ).scalar_one_or_none()
        if existing_event is None:
            db.session.add(
                Event(
                    code=configured_code,
                    name=app.config["EVENT_NAME"],
                    starts_at=app.config["CHECKIN_START_DATE"],
                )
            )
            db.session.commit()
        click.echo("Database tables created.")

    @app.cli.command("import-guests")
    @click.argument("csv_path", type=click.Path(exists=True, dir_okay=False))
    def import_guests_command(csv_path):
        """Import guests from a first_name,last_name,email CSV file."""
        created = 0
        skipped_duplicate = 0
        skipped_invalid = 0
        seen_emails = set()

        with open(csv_path, newline="", encoding="utf-8-sig") as csv_file:
            reader = csv.DictReader(csv_file)
            required = {"first_name", "last_name", "email"}
            if not required.issubset(reader.fieldnames or []):
                raise click.ClickException(
                    "CSV must contain first_name, last_name, and email columns."
                )

            for row_number, row in enumerate(reader, start=2):
                email = (row.get("email") or "").strip().lower()
                first_name = (row.get("first_name") or "").strip()
                last_name = (row.get("last_name") or "").strip()
                if not email or "@" not in email or not (first_name or last_name):
                    click.echo(f"Skipping invalid row {row_number}.", err=True)
                    skipped_invalid += 1
                    continue

                if email in seen_emails:
                    click.echo(f"Skipping duplicate CSV email on row {row_number}: {email}")
                    skipped_duplicate += 1
                    continue
                seen_emails.add(email)

                existing = db.session.execute(
                    db.select(Guest).where(db.func.lower(Guest.email) == email)
                ).scalar_one_or_none()
                if existing:
                    click.echo(f"Skipping existing guest: {email}")
                    skipped_duplicate += 1
                    continue

                digest = hashlib.sha256(email.encode("utf-8")).hexdigest()[:10].upper()
                db.session.add(
                    Guest(
                        name=" ".join(part for part in (first_name, last_name) if part),
                        email=email,
                        unique_id=f"GTHR-{digest}",
                    )
                )
                created += 1

        db.session.commit()
        click.echo(
            f"Import complete: {created} created, {skipped_duplicate} duplicates "
            f"skipped, {skipped_invalid} invalid rows skipped."
        )

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Route not found."}}), 404

    return app
