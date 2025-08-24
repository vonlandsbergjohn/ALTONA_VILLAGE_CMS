# src/routes/admin_notifications.py
# Admin Notifications Route - Track Critical User Updates (SQLAlchemy version)

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps
from datetime import datetime
from typing import Optional

from sqlalchemy import case, desc
from src.models.user import db, User, Resident, Owner  # include Resident/Owner to resolve ERF
from src.models.user_change import UserChange  # the model/table

admin_notifications = Blueprint('admin_notifications', __name__)

# ---------------------------- helpers ---------------------------------
def admin_required(f):
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        uid = get_jwt_identity()
        u = User.query.get(uid)
        if not u or u.role != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated


def _resolve_erf_for_user(user_id: str) -> Optional[str]:
    """
    Best-effort ERF resolver if a change comes in without an explicit erf_number.
    Looks on the user's Resident first, then Owner.
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return None
        # Prefer resident ERF if present
        if getattr(user, "resident", None) and getattr(user.resident, "erf_number", None):
            return user.resident.erf_number
        if getattr(user, "owner", None) and getattr(user.owner, "erf_number", None):
            return user.owner.erf_number
    except Exception:
        pass
    return None


def serialize_change(c: UserChange) -> dict:
    erf = getattr(c, "erf_number", None)
    return {
        "id": c.id,
        "user_id": c.user_id,
        "change_type": c.change_type,
        "field_name": c.field_name,
        "old_value": c.old_value,
        "new_value": c.new_value,
        "change_timestamp": (c.change_timestamp.isoformat() if c.change_timestamp else None),
        "admin_reviewed": bool(c.admin_reviewed),
        # ERF for UI
        "erf_number": erf,
        "erf": erf,
    }


# Keep the signature used by admin.py, but now store erf_number too
def log_user_change(user_id, user_name, erf_number, change_type, field_name, old_value, new_value):
    try:
        erf = erf_number or _resolve_erf_for_user(user_id)

        change = UserChange(
            user_id=str(user_id),
            field_name=str(field_name),
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            change_type=str(change_type or "update"),
            change_timestamp=datetime.utcnow(),
            admin_reviewed=False,
            erf_number=str(erf) if erf else None,
        )
        db.session.add(change)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        # Don’t crash the caller; just report failure
        print(f"[log_user_change] failed: {e}")
        return False


# ----------------------------- routes ---------------------------------

@admin_notifications.route("/admin/changes/stats", methods=["GET"])
@admin_required
def get_change_stats():
    """Counts used by the dashboard."""
    try:
        # today
        today_count = UserChange.query.filter(
            db.func.date(UserChange.change_timestamp) == db.func.current_date()
        ).count()

        # last 7 days
        week_count = UserChange.query.filter(
            UserChange.change_timestamp >= db.func.datetime(db.func.current_timestamp(), "-7 days")
        ).count()

        critical_fields = ("cellphone_number", "vehicle_registration", "vehicle_registration_2")

        critical_pending = UserChange.query.filter(
            UserChange.field_name.in_(critical_fields),
            UserChange.admin_reviewed.is_(False),
        ).count()

        non_critical_pending = UserChange.query.filter(
            ~UserChange.field_name.in_(critical_fields),
            UserChange.admin_reviewed.is_(False),
        ).count()

        total_pending = UserChange.query.filter(
            UserChange.admin_reviewed.is_(False)
        ).count()

        # breakdowns
        by_change_type = {
            k: v for k, v in db.session.query(
                UserChange.change_type, db.func.count(UserChange.id)
            ).filter(
                UserChange.admin_reviewed.is_(False)
            ).group_by(UserChange.change_type).all()
        }

        by_field_name = {
            k: v for k, v in db.session.query(
                UserChange.field_name, db.func.count(UserChange.id)
            ).filter(
                UserChange.admin_reviewed.is_(False)
            ).group_by(UserChange.field_name).order_by(db.func.count(UserChange.id).desc()).all()
        }

        return jsonify({
            "success": True,
            "stats": {
                "today": today_count,
                "this_week": week_count,
                "critical_pending": critical_pending,
                "non_critical_pending": non_critical_pending,
                "total_pending": total_pending,
                "by_change_type": by_change_type,
                "by_field_name": by_field_name,
            }
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get stats: {e}"}), 500


@admin_notifications.route("/admin/changes/critical", methods=["GET"])
@admin_required
def get_critical_changes():
    try:
        critical_fields = ("cellphone_number", "vehicle_registration", "vehicle_registration_2")
        rows = UserChange.query.filter(
            UserChange.field_name.in_(critical_fields),
            UserChange.admin_reviewed.is_(False),
        ).order_by(UserChange.change_timestamp.desc()).all()

        # Backfill ERF in the payload if older rows predate the new column
        out = []
        for r in rows:
            if not getattr(r, "erf_number", None):
                r.erf_number = _resolve_erf_for_user(r.user_id)
            out.append(serialize_change(r))

        return jsonify({
            "success": True,
            "critical_changes": out,
            "count": len(out),
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch critical changes: {e}"}), 500


@admin_notifications.route("/admin/changes/non-critical", methods=["GET"])
@admin_required
def get_non_critical_changes():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        show_reviewed = request.args.get("show_reviewed", "false").lower() == "true"

        q = UserChange.query.filter(~UserChange.field_name.in_(
            ("cellphone_number", "vehicle_registration", "vehicle_registration_2")
        ))
        if not show_reviewed:
            q = q.filter(UserChange.admin_reviewed.is_(False))

        total = q.count()
        rows = q.order_by(UserChange.change_timestamp.desc()) \
                .limit(per_page).offset((page - 1) * per_page).all()

        total_pages = (total + per_page - 1) // per_page

        out = []
        for r in rows:
            if not getattr(r, "erf_number", None):
                r.erf_number = _resolve_erf_for_user(r.user_id)
            out.append(serialize_change(r))

        return jsonify({
            "success": True,
            "non_critical_changes": out,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_count": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
            "count": len(out),
            "total_pending": total,
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch non-critical changes: {e}"}), 500


@admin_notifications.route("/admin/changes/pending", methods=["GET"])
@admin_required
def get_pending_changes():
    """All unreviewed changes, critical first."""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)

        priority = case(
            (
                UserChange.field_name.in_(("cellphone_number", "vehicle_registration", "vehicle_registration_2")),
                0
            ),
            else_=1
        )

        q = UserChange.query.filter(UserChange.admin_reviewed.is_(False))
        total = q.count()
        rows = q.order_by(priority, desc(UserChange.change_timestamp)) \
                .limit(per_page).offset((page - 1) * per_page).all()

        total_pages = (total + per_page - 1) // per_page

        # critical count
        critical_count = UserChange.query.filter(
            UserChange.admin_reviewed.is_(False),
            UserChange.field_name.in_(("cellphone_number", "vehicle_registration", "vehicle_registration_2")),
        ).count()

        out = []
        for r in rows:
            if not getattr(r, "erf_number", None):
                r.erf_number = _resolve_erf_for_user(r.user_id)
            out.append(serialize_change(r))

        return jsonify({
            "success": True,
            "changes": out,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_count": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
            "total_pending": total,
            "critical_pending": critical_count,
            "showing_count": len(out),
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get pending changes: {e}"}), 500


@admin_notifications.route("/admin/changes/review", methods=["POST"])
@admin_required
def review_changes():
    """Mark changes as reviewed (simple boolean toggle)."""
    try:
        change_ids = (request.json or {}).get("change_ids", [])
        if not change_ids:
            return jsonify({"error": "No change IDs provided"}), 400

        # Update in bulk
        UserChange.query.filter(UserChange.id.in_(change_ids)).update(
            {UserChange.admin_reviewed: True}, synchronize_session=False
        )
        db.session.commit()
        return jsonify({"success": True, "message": f"Reviewed {len(change_ids)} changes"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to review changes: {e}"}), 500
