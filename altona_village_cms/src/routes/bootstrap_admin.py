# altona_village_cms/src/routes/bootstrap_admin.py
from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash
from ..models.user import db, User, Resident

bootstrap_bp = Blueprint("bootstrap", __name__)

# ---------------------------------------------------------------------
# Helper: shared header check (same as before, using BOOTSTRAP_KEY)
# ---------------------------------------------------------------------
def _ok():
    return (
        request.headers.get("X-Setup-Key")
        and request.headers.get("X-Setup-Key") == current_app.config.get("BOOTSTRAP_KEY")
    )

# ---------------------------------------------------------------------
# 1) EXISTING: create/upgrade an admin user (unchanged)
# ---------------------------------------------------------------------
@bootstrap_bp.route("/api/_bootstrap_admin", methods=["POST"])
def bootstrap_admin():
    if not _ok():
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
        # Set every approval/active flag your model might have
        if hasattr(u, "status"): u.status = "active"
        if hasattr(u, "is_active"): u.is_active = True
        if hasattr(u, "approved"): u.approved = True
        if hasattr(u, "is_approved"): u.is_approved = True
        if hasattr(u, "approval_status"): u.approval_status = "approved"
        u.password_hash = generate_password_hash(password)

    db.session.commit()
    return jsonify({"ok": True, "updated": len(users)})

# ---------------------------------------------------------------------
# 2) NEW: make sure the UserChange table exists on Render Postgres
# ---------------------------------------------------------------------
@bootstrap_bp.route("/api/_ensure_change_table", methods=["POST"])
def ensure_change_table():
    if not _ok():
        return jsonify({"error": "unauthorized"}), 401
    try:
        # Import inside so the route is safe even if the model moves
        from src.models.user_change import UserChange
        # Create only if missing (no-op if it already exists)
        UserChange.__table__.create(db.engine, checkfirst=True)
        return jsonify({"ok": True})
    except Exception as e:
        current_app.logger.exception("ensure_change_table failed")
        return jsonify({"ok": False, "error": str(e)}), 500

# ---------------------------------------------------------------------
# 3) NEW: write an Intercom Code to the Resident row for a given ERF
#    (this is the single source of truth used by Gate Register + banner)
# ---------------------------------------------------------------------
@bootstrap_bp.route("/api/_set_intercom", methods=["POST"])
def set_intercom():
    if not _ok():
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip()
    erf_number = (data.get("erf_number") or "").strip()
    intercom_code = (data.get("intercom_code") or "").strip()

    if not email or not erf_number or not intercom_code:
        return jsonify({"error": "email, erf_number, intercom_code are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    # Find the resident record for THIS user + ERF
    res = None
    if user.resident and user.resident.erf_number == erf_number:
        res = user.resident
    else:
        res = Resident.query.filter_by(user_id=user.id, erf_number=erf_number).first()

    if not res:
        return jsonify({"error": "resident record for that ERF not found"}), 404

    res.intercom_code = intercom_code
    db.session.commit()

    # Return a minimal echo so you can see what’s saved
    return jsonify({
        "ok": True,
        "resident": {
            "id": res.id,
            "erf_number": res.erf_number,
            "first_name": res.first_name,
            "last_name": res.last_name,
            "intercom_code": res.intercom_code
        }
    }), 200

# ---------------------------------------------------------------------
# 4) NEW (optional): quick debug for a user -> shows current resident/owner
# ---------------------------------------------------------------------
@bootstrap_bp.route("/api/_debug_user", methods=["GET"])
def debug_user():
    if not _ok():
        return jsonify({"error": "unauthorized"}), 401
    email = (request.args.get("email") or "").strip()
    if not email:
        return jsonify({"error": "email required"}), 400
    u = User.query.filter_by(email=email).first()
    if not u:
        return jsonify({"error": "user not found"}), 404

    out = {
        "id": u.id,
        "email": u.email,
        "role": u.role,
        "status": u.status,
        "resident": None,
        "owner": None,
    }
    if u.resident:
        r = u.resident
        out["resident"] = {
            "id": r.id,
            "erf_number": r.erf_number,
            "first_name": r.first_name,
            "last_name": r.last_name,
            "intercom_code": r.intercom_code,
        }
    if u.owner:
        o = u.owner
        out["owner"] = {
            "id": o.id,
            "erf_number": o.erf_number,
            "first_name": o.first_name,
            "last_name": o.last_name,
        }
    return jsonify({"ok": True, "user": out})
