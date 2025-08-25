# src/routes/user_management.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import or_, and_

from ..models.user import db, User, Resident, Owner, Vehicle

user_management_bp = Blueprint("user_management", __name__)

# --------------------------- helpers ---------------------------

def _require_admin():
    """Return (current_user, error_response) where error_response is a Flask response or None."""
    cur = User.query.get(get_jwt_identity())
    if not cur or cur.role != "admin":
        return None, (jsonify({"error": "Admin access required"}), 403)
    return cur, None


# --------------------------- queries ---------------------------

@user_management_bp.route("/admin/users/inactive", methods=["GET"])
@jwt_required()
def get_inactive_users():
    """Get all inactive users (not archived yet)."""
    try:
        _, err = _require_admin()
        if err:
            return err

        inactive_users = User.query.filter(
            and_(User.status == "inactive", or_(User.archived == False, User.archived.is_(None)))
        ).all()

        users_data = []
        for user in inactive_users:
            user_data = user.to_dict()

            erfs = []
            if user.resident:
                erfs.append({
                    "erf_number": user.resident.erf_number,
                    "type": "resident",
                    "migration_date": user.resident.migration_date.isoformat() if user.resident.migration_date else None,
                    "migration_reason": user.resident.migration_reason,
                })
            if user.owner:
                erfs.append({
                    "erf_number": user.owner.erf_number,
                    "type": "owner",
                    "migration_date": user.owner.migration_date.isoformat() if user.owner.migration_date else None,
                    "migration_reason": user.owner.migration_reason,
                })

            user_data["erfs"] = erfs
            users_data.append(user_data)

        return jsonify({"users": users_data, "total": len(users_data)}), 200

    except Exception as e:
        current_app.logger.error(f"Error fetching inactive users: {e}")
        return jsonify({"error": "Failed to fetch inactive users"}), 500


@user_management_bp.route("/admin/users/archived", methods=["GET"])
@jwt_required()
def get_archived_users():
    """Get all archived users."""
    try:
        _, err = _require_admin()
        if err:
            return err

        archived_users = User.query.filter(User.archived == True).all()

        users_data = []
        for user in archived_users:
            user_data = user.to_dict()

            erfs = []
            if user.resident:
                erfs.append({
                    "erf_number": user.resident.erf_number,
                    "type": "resident",
                    "migration_date": user.resident.migration_date.isoformat() if user.resident.migration_date else None,
                    "migration_reason": user.resident.migration_reason,
                })
            if user.owner:
                erfs.append({
                    "erf_number": user.owner.erf_number,
                    "type": "owner",
                    "migration_date": user.owner.migration_date.isoformat() if user.owner.migration_date else None,
                    "migration_reason": user.owner.migration_reason,
                })

            if user.archived_by:
                archived_by_user = User.query.get(user.archived_by)
                user_data["archived_by_user"] = archived_by_user.get_full_name() if archived_by_user else "Unknown"

            user_data["erfs"] = erfs
            users_data.append(user_data)

        return jsonify({"users": users_data, "total": len(users_data)}), 200

    except Exception as e:
        current_app.logger.error(f"Error fetching archived users: {e}")
        return jsonify({"error": "Failed to fetch archived users"}), 500


# --------------------------- archive actions ---------------------------

@user_management_bp.route("/admin/users/<user_id>/archive", methods=["POST"])
@jwt_required()
def archive_user(user_id):
    """Archive an inactive user."""
    try:
        current_admin, err = _require_admin()
        if err:
            return err

        user = User.query.get_or_404(user_id)

        if user.status != "inactive":
            return jsonify({"error": "Can only archive inactive users"}), 400
        if user.archived:
            return jsonify({"error": "User is already archived"}), 400

        data = request.get_json() or {}
        archive_reason = data.get("reason", "Archived by admin")

        user.archived = True
        user.archived_at = datetime.utcnow()
        user.archived_by = current_admin.id
        user.archive_reason = archive_reason
        user.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            "message": f"User {user.get_full_name()} archived successfully",
            "user_id": user_id,
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error archiving user: {e}")
        return jsonify({"error": "Failed to archive user"}), 500


@user_management_bp.route("/admin/users/<user_id>/unarchive", methods=["POST"])
@jwt_required()
def unarchive_user(user_id):
    """Unarchive a user (restore to inactive status)."""
    try:
        _, err = _require_admin()
        if err:
            return err

        user = User.query.get_or_404(user_id)

        if not user.archived:
            return jsonify({"error": "User is not archived"}), 400

        user.archived = False
        user.archived_at = None
        user.archived_by = None
        user.archive_reason = None
        user.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            "message": f"User {user.get_full_name()} unarchived successfully",
            "user_id": user_id,
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error unarchiving user: {e}")
        return jsonify({"error": "Failed to unarchive user"}), 500


@user_management_bp.route("/admin/users/<user_id>/delete", methods=["DELETE"])
@jwt_required()
def permanently_delete_user(user_id):
    """Permanently delete an archived user and all related data."""
    try:
        _, err = _require_admin()
        if err:
            return err

        user = User.query.get_or_404(user_id)

        if not user.archived:
            return jsonify({"error": "User must be archived before permanent deletion"}), 400

        data = request.get_json() or {}
        if not data.get("confirm", False):
            return jsonify({"error": "Deletion confirmation required"}), 400

        user_name = user.get_full_name()
        user_email = user.email

        # collect ERFs for response
        erfs = []
        if user.resident:
            erfs.append(f"Resident ERF {user.resident.erf_number}")
        if user.owner:
            erfs.append(f"Owner ERF {user.owner.erf_number}")

        # delete vehicles (resident and owner)
        if user.resident:
            for v in Vehicle.query.filter_by(resident_id=user.resident.id).all():
                db.session.delete(v)
        if user.owner:
            for v in Vehicle.query.filter_by(owner_id=user.owner.id).all():
                db.session.delete(v)

        db.session.delete(user)
        db.session.commit()

        return jsonify({
            "message": f"User {user_name} ({user_email}) permanently deleted",
            "deleted_user": {"name": user_name, "email": user_email, "erfs": erfs},
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error permanently deleting user: {e}")
        return jsonify({"error": "Failed to permanently delete user"}), 500


@user_management_bp.route("/admin/users/archive-old", methods=["POST"])
@jwt_required()
def archive_old_inactive_users():
    """Archive all inactive users older than specified days."""
    try:
        current_admin, err = _require_admin()
        if err:
            return err

        data = request.get_json() or {}
        days_threshold = data.get("days", 30)
        archive_reason = data.get("reason", f"Auto-archived: inactive for {days_threshold}+ days")

        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)

        old_inactive_users = User.query.filter(
            and_(
                User.status == "inactive",
                or_(User.archived == False, User.archived.is_(None)),
                User.updated_at < cutoff_date,
            )
        ).all()

        archived_count = 0
        archived_users = []

        for user in old_inactive_users:
            user.archived = True
            user.archived_at = datetime.utcnow()
            user.archived_by = current_admin.id
            user.archive_reason = archive_reason
            user.updated_at = datetime.utcnow()

            archived_users.append({
                "id": user.id,
                "name": user.get_full_name(),
                "email": user.email,
                "inactive_since": user.updated_at.isoformat() if user.updated_at else None,
            })
            archived_count += 1

        db.session.commit()

        return jsonify({
            "message": f"Archived {archived_count} inactive users",
            "archived_users": archived_users,
            "days_threshold": days_threshold,
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error archiving old inactive users: {e}")
        return jsonify({"error": "Failed to archive old users"}), 500


# --------------------------- INTERCOM CODE (admin-only) ---------------------------

@user_management_bp.route("/admin/users/<user_id>/intercom", methods=["PUT"])
@jwt_required()
def set_intercom_code(user_id):
    """
    Admin sets or updates the intercom code for a user's RESIDENT record.
    This does NOT log a notification (admin-initiated change).
    Body: { "intercom_code": "12345" }
    """
    try:
        _, err = _require_admin()
        if err:
            return err

        user = User.query.get_or_404(user_id)
        data = request.get_json() or {}
        code = (data.get("intercom_code") or "").strip()

        if not code:
            return jsonify({"error": "intercom_code is required"}), 400

        # Prefer resident (intercom is conceptually tied to occupancy)
        if not user.resident:
            return jsonify({"error": "User has no resident profile to attach intercom code"}), 400

        user.resident.intercom_code = code
        # keep some useful mirrors current if your UI expects them
        user.updated_at = datetime.utcnow()
        if hasattr(user.resident, "updated_at"):
            user.resident.updated_at = datetime.utcnow()

        db.session.commit()

        # Return minimal payload used by your UI (adjust if you need more)
        return jsonify({
            "message": "Intercom code updated",
            "user_id": user.id,
            "erf_number": user.resident.erf_number,
            "intercom_code": user.resident.intercom_code,
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error setting intercom code: {e}")
        return jsonify({"error": "Failed to set intercom code"}), 500
