# altona_village_cms/src/routes/bootstrap_admin.py
from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash
from ..models.user import db, User
import hmac

bootstrap_bp = Blueprint("bootstrap", __name__)

def _get_boot_keys():
    """Return (expected_key, supplied_key) with safe trimming and fallbacks."""
    expected = (current_app.config.get("BOOTSTRAP_KEY") or "").strip()

    # 1) Preferred: custom header
    supplied = (request.headers.get("X-Setup-Key") or "").strip()

    # 2) Fallbacks: JSON body or query string
    if not supplied:
        payload = request.get_json(silent=True) or {}
        supplied = (payload.get("setup_key") or payload.get("key") or "").strip()
    if not supplied:
        supplied = (request.args.get("setup_key") or request.args.get("key") or "").strip()

    return expected, supplied

@bootstrap_bp.route("/api/_bootstrap_admin", methods=["POST"])
def bootstrap_admin():
    expected, supplied = _get_boot_keys()
    if not expected:
        return jsonify({"error": "bootstrap disabled"}), 403
    if not supplied or not hmac.compare_digest(expected, supplied):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return jsonify({"error": "email and password required"}), 400

    users = User.query.filter_by(email=email).all()
    if not users:
        u = User(email=email)
        db.session.add(u)
        users = [u]

    for u in users:
        u.role = "admin"
        if hasattr(u, "status"):           u.status = "active"
        if hasattr(u, "is_active"):        u.is_active = True
        if hasattr(u, "approved"):         u.approved = True
        if hasattr(u, "is_approved"):      u.is_approved = True
        if hasattr(u, "approval_status"):  u.approval_status = "approved"
        u.password_hash = generate_password_hash(password)

    db.session.commit()
    return jsonify({"ok": True, "updated": len(users)})
