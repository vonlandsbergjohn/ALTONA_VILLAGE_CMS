# altona_village_cms/src/routes/bootstrap_admin.py
from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash
from ..models.user import db, User

bootstrap_bp = Blueprint("bootstrap", __name__)

@bootstrap_bp.route("/api/_bootstrap_admin", methods=["POST"])
def bootstrap_admin():
    # Read expected key from config
    expected = (current_app.config.get("BOOTSTRAP_KEY") or "").strip()

    # Accept the provided key from header, query, or JSON body (any one)
    payload = request.get_json(silent=True) or {}
    provided = (
        request.headers.get("X-Setup-Key")
        or request.args.get("key")
        or payload.get("setup_key")
        or ""
    ).strip()

    if not expected or provided != expected:
        return jsonify({"error": "unauthorized"}), 401

    email = payload.get("email")
    password = payload.get("password")
    if not email or not password:
        return jsonify({"error": "email and password required"}), 400

    users = User.query.filter_by(email=email).all()
    if not users:
        u = User(email=email)
        db.session.add(u)
        users = [u]

    for u in users:
        u.role = "admin"
        # Flip every likely approval/active flag
        if hasattr(u, "status"): u.status = "active"
        if hasattr(u, "is_active"): u.is_active = True
        if hasattr(u, "approved"): u.approved = True
        if hasattr(u, "is_approved"): u.is_approved = True
        if hasattr(u, "approval_status"): u.approval_status = "approved"
        u.password_hash = generate_password_hash(password)

    db.session.commit()
    return jsonify({"ok": True, "updated": len(users)})
