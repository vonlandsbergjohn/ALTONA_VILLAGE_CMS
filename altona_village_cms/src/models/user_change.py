# src/models/user_change.py
from datetime import datetime
from src.models.user import db

class UserChange(db.Model):
    __tablename__ = "user_changes"

    id = db.Column(db.Integer, primary_key=True)

    # keep as string so it works with UUIDs too
    user_id   = db.Column(db.String(64), nullable=False)
    user_name = db.Column(db.String(255))
    erf_number = db.Column(db.String(64))

    change_type = db.Column(db.String(64), nullable=False, default="update")
    field_name  = db.Column(db.String(128), nullable=False)
    old_value   = db.Column(db.Text)
    new_value   = db.Column(db.Text)

    change_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    admin_reviewed = db.Column(db.Boolean, nullable=False, default=False)
    admin_reviewer = db.Column(db.String(255))
    review_timestamp = db.Column(db.DateTime)

    exported_to_external = db.Column(db.Boolean, nullable=False, default=False)
    export_timestamp     = db.Column(db.DateTime)

    notes = db.Column(db.Text)

    __table_args__ = (
        db.Index("ix_user_changes_ts", "change_timestamp"),
        db.Index("ix_user_changes_reviewed_ts", "admin_reviewed", "change_timestamp"),
    )

def ensure_user_changes_table():
    """Create the table if it doesn't exist (idempotent)."""
    db.create_all()
