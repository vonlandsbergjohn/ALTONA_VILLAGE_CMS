# src/models/user_change.py
from datetime import datetime

from flask import current_app
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Engine

from .user import db


class UserChange(db.Model):
    """
    Records changes made by users that may require admin review/sync.
    """
    __tablename__ = "user_changes"

    id = db.Column(db.Integer, primary_key=True)

    # who changed
    user_id = db.Column(db.String(64), nullable=False)

    # what changed
    change_type = db.Column(db.String(50))
    field_name  = db.Column(db.String(100))
    old_value   = db.Column(db.Text)
    new_value   = db.Column(db.Text)

    # when
    change_timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # review status
    admin_reviewed = db.Column(db.Boolean, default=False, nullable=False)

    # NEW: related ERF (nullable for legacy rows)
    erf_number = db.Column(db.String(64), nullable=True)


def _add_column_if_missing(engine: Engine, table: str, column: str,
                           ddl_sqlite: str, ddl_pg: str) -> None:
    insp = db.inspect(engine)
    existing_cols = {c["name"] for c in insp.get_columns(table)}
    if column in existing_cols:
        return

    dialect = engine.dialect.name
    ddl = ddl_sqlite if dialect == "sqlite" else ddl_pg
    with engine.begin() as conn:
        conn.execute(text(ddl))


def ensure_user_changes_table() -> None:
    """
    Create the user_changes table if missing, and ensure the erf_number column exists.
    Called once at app startup from main.py.
    """
    try:
        engine = db.engine
        insp = db.inspect(engine)
        tables = set(insp.get_table_names())

        if "user_changes" not in tables:
            UserChange.__table__.create(bind=engine)
            current_app.logger.info("Created table user_changes")

        _add_column_if_missing(
            engine,
            "user_changes",
            "erf_number",
            "ALTER TABLE user_changes ADD COLUMN erf_number TEXT",
            "ALTER TABLE user_changes ADD COLUMN IF NOT EXISTS erf_number VARCHAR(64)",
        )

        current_app.logger.info("user_changes table OK (schema up-to-date)")
    except SQLAlchemyError as e:
        try:
            current_app.logger.exception("Failed to ensure user_changes table: %s", e)
        except Exception:
            print(f"[ensure_user_changes_table] failed: {e}")
