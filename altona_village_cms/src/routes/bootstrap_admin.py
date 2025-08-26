# altona_village_cms/src/routes/bootstrap_admin.py
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import text, inspect
from src.models.user import db, User
from werkzeug.security import generate_password_hash

bootstrap_bp = Blueprint("bootstrap", __name__)

def _authorized():
    return request.headers.get("X-Setup-Key") == current_app.config.get("BOOTSTRAP_KEY")

@bootstrap_bp.route("/api/_bootstrap_admin", methods=["POST"])
def bootstrap_admin():
    if not _authorized():
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(force=True) or {}
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "email and password required"}), 400

    users = User.query.filter_by(email=email).all()
    if not users:
        u = User(email=email)
        db.session.add(u)
        users = [u]

    for u in users:
        u.role = "admin"
        if hasattr(u, "status"): u.status = "active"
        if hasattr(u, "is_active"): u.is_active = True
        if hasattr(u, "approved"): u.approved = True
        if hasattr(u, "is_approved"): u.is_approved = True
        if hasattr(u, "approval_status"): u.approval_status = "approved"
        u.password_hash = generate_password_hash(password)

    db.session.commit()
    return jsonify({"ok": True, "updated": len(users)})

@bootstrap_bp.route("/api/_ensure_change_table", methods=["POST"])
def ensure_change_table():
    """Create the user_changes table if it doesn't exist (baseline)."""
    if not _authorized():
        return jsonify({"error": "unauthorized"}), 401

    ddl = """
    CREATE TABLE IF NOT EXISTS user_changes (
        id               SERIAL PRIMARY KEY,
        user_id          VARCHAR(64) NOT NULL,
        change_type      VARCHAR(64),
        field_name       VARCHAR(128),
        old_value        TEXT,
        new_value        TEXT,
        change_timestamp TIMESTAMPTZ DEFAULT NOW(),
        admin_reviewed   BOOLEAN DEFAULT FALSE,
        erf_number       VARCHAR(64)
    );
    """
    db.session.execute(text(ddl))
    db.session.commit()
    return jsonify({"ok": True})

@bootstrap_bp.route("/api/_patch_user_changes", methods=["POST"])
def patch_user_changes():
    """
    Make sure ALL expected columns exist.
    Safe to run repeatedly.
    """
    if not _authorized():
        return jsonify({"error": "unauthorized"}), 401

    # Create if missing (idempotent)
    db.session.execute(text("""
    CREATE TABLE IF NOT EXISTS user_changes (
        id               SERIAL PRIMARY KEY,
        user_id          VARCHAR(64) NOT NULL,
        change_type      VARCHAR(64),
        field_name       VARCHAR(128),
        old_value        TEXT,
        new_value        TEXT,
        change_timestamp TIMESTAMPTZ DEFAULT NOW(),
        admin_reviewed   BOOLEAN DEFAULT FALSE,
        erf_number       VARCHAR(64)
    );
    """))

    # Patch columns if they don't exist
    alters = [
        "ALTER TABLE user_changes ADD COLUMN IF NOT EXISTS user_id VARCHAR(64) NOT NULL;",
        "ALTER TABLE user_changes ADD COLUMN IF NOT EXISTS change_type VARCHAR(64);",
        "ALTER TABLE user_changes ADD COLUMN IF NOT EXISTS field_name VARCHAR(128);",
        "ALTER TABLE user_changes ADD COLUMN IF NOT EXISTS old_value TEXT;",
        "ALTER TABLE user_changes ADD COLUMN IF NOT EXISTS new_value TEXT;",
        "ALTER TABLE user_changes ADD COLUMN IF NOT EXISTS change_timestamp TIMESTAMPTZ DEFAULT NOW();",
        "ALTER TABLE user_changes ADD COLUMN IF NOT EXISTS admin_reviewed BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE user_changes ADD COLUMN IF NOT EXISTS erf_number VARCHAR(64);",
    ]
    for stmt in alters:
        db.session.execute(text(stmt))

    db.session.commit()

    # Return current columns so you can see what's there
    insp = inspect(db.engine)
    cols = [c["name"] for c in insp.get_columns("user_changes")]
    return jsonify({"ok": True, "columns": cols})

@bootstrap_bp.route("/api/_debug_changes", methods=["GET"])
def debug_changes():
    if not _authorized():
        return jsonify({"error": "unauthorized"}), 401
    insp = inspect(db.engine)
    cols = [c["name"] for c in insp.get_columns("user_changes")]
    count = db.session.execute(text("SELECT COUNT(*) FROM user_changes")).scalar()
    return jsonify({"ok": True, "columns": cols, "row_count": count})
