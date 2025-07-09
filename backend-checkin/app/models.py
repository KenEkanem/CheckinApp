from .extensions import db


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), nullable=False, unique=True, index=True)
    name = db.Column(db.String(255), nullable=False)
    starts_at = db.Column(db.DateTime(timezone=True), nullable=True)
    venue = db.Column(db.String(255), nullable=True)
    doors_open = db.Column(db.String(100), nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=db.func.now()
    )

    def to_dict(self):
        return {
            "name": self.name,
            "code": self.code,
            "startsAt": self.starts_at.isoformat() if self.starts_at else None,
            "venue": self.venue,
            "doorsOpen": self.doors_open,
        }


class Guest(db.Model):
    __tablename__ = "guests"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(320), nullable=False, unique=True, index=True)
    unique_id = db.Column(db.String(100), nullable=False, unique=True, index=True)
    group = db.Column("xn", db.String(50), nullable=True)
    time_checked_in = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=db.func.now()
    )

    def to_dict(self):
        return {
            "name": self.name,
            "email": self.email,
            "uniqueId": self.unique_id,
            "group": self.group,
            "checkedInAt": (
                self.time_checked_in.isoformat() if self.time_checked_in else None
            ),
        }
