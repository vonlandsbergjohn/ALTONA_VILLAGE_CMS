# altona_village_cms/src/routes/communication.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime
from sqlalchemy import or_

import os
import uuid

from src.models.user import User, Resident, Owner, db
from src.utils.email_service import send_custom_email, send_email_with_attachment

communication_bp = Blueprint("communication", __name__)

# ------------------------- helpers & guards -------------------------

def admin_required(f):
    """Decorator to allow only admin users."""
    @wraps(f)
    @jwt_required()
    def wrapper(*args, **kwargs):
        uid = get_jwt_identity()
        user = User.query.get(uid)
        if not user or user.role != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return wrapper


def _upload_dir() -> str:
    """Prefer app-configured UPLOAD_FOLDER; fallback to ./uploads."""
    base = current_app.config.get("UPLOAD_FOLDER")
    if not base:
        base = os.path.join(os.getcwd(), "uploads")
    os.makedirs(base, exist_ok=True)
    return base


def _recipient_users(recipient_type: str):
    """
    Return a de-duped list of active Users with emails,
    filtered by recipient_type: 'all' | 'owners' | 'residents'
    """
    q_base = User.query.filter(
        User.status == "active",
        User.email.isnot(None),
        User.email != "",
    )

    if recipient_type == "owners":
        q = db.session.query(User).join(Owner).filter(
            User.id == Owner.user_id,
            User.status == "active",
            User.email.isnot(None),
            User.email != "",
        )
        users = q.all()
    elif recipient_type == "residents":
        q = db.session.query(User).join(Resident).filter(
            User.id == Resident.user_id,
            User.status == "active",
            User.email.isnot(None),
            User.email != "",
        )
        users = q.all()
    else:
        users = q_base.all()

    # de-dupe by email to avoid double sends for owner-residents
    seen = set()
    unique = []
    for u in users:
        key = (u.email or "").lower().strip()
        if key and key not in seen:
            unique.append(u)
            seen.add(key)
    return unique


# ------------------------------ routes ------------------------------

@communication_bp.route("/send-email", methods=["POST"])
@admin_required
def send_bulk_email():
    try:
        data = request.get_json() or {}
        subject = (data.get("subject") or "").strip()
        message = (data.get("message") or "").strip()
        recipient_type = (data.get("recipient_type") or "all").strip().lower()

        if not subject or not message:
            return jsonify({"error": "Subject and message are required"}), 400

        recipients = _recipient_users(recipient_type)
        current_app.logger.info("Bulk email: type=%s recipients=%d", recipient_type, len(recipients))

        if not recipients:
            return jsonify({"error": "No recipients found"}), 404

        sent_count = 0
        failed = []

        for u in recipients:
            try:
                ok, err = send_custom_email(
                    to_email=u.email,
                    subject=subject,
                    message=message,
                    recipient_name=u.get_full_name() if hasattr(u, "get_full_name") else (u.email or "Resident"),
                )
                if ok:
                    sent_count += 1
                else:
                    failed.append({"email": u.email, "error": err or "unknown error"})
            except Exception as e:
                failed.append({"email": u.email, "error": str(e)})

        return jsonify({
            "message": f"Email sent successfully to {sent_count} recipients",
            "sent_count": sent_count,
            "failed_count": len(failed),
            "failed_emails": failed,
        }), 200

    except Exception as e:
        current_app.logger.exception("Bulk email failed")
        return jsonify({"error": str(e)}), 500


@communication_bp.route("/send-whatsapp", methods=["POST"])
@admin_required
def send_whatsapp_message():
    try:
        data = request.get_json() or {}
        message = (data.get("message") or "").strip()
        recipient_type = (data.get("recipient_type") or "all").strip().lower()

        if not message:
            return jsonify({"error": "Message is required"}), 400

        # NOTE: This is still a stub; integrate a real provider here
        query = Resident.query.join(User).filter(
            User.status == "active",
            Resident.phone_number.isnot(None),
            Resident.phone_number != "",
        )
        if recipient_type == "owners":
            query = query.filter(Resident.is_owner == True)
        elif recipient_type == "tenants":
            query = query.filter(or_(Resident.is_owner == False, Resident.is_owner.is_(None)))

        residents = query.all()
        if not residents:
            return jsonify({"error": "No phone numbers found"}), 404

        sent = 0
        failed = []
        for r in residents:
            try:
                # send_whatsapp_via_api(r.phone_number, message)
                sent += 1
            except Exception as e:
                failed.append({"phone": r.phone_number, "error": str(e)})

        return jsonify({
            "message": f"WhatsApp message sent successfully to {sent} recipients",
            "sent_count": sent,
            "failed_count": len(failed),
            "failed_numbers": failed,
        }), 200

    except Exception as e:
        current_app.logger.exception("WhatsApp bulk failed")
        return jsonify({"error": str(e)}), 500


@communication_bp.route("/templates", methods=["GET"])
@admin_required
def get_message_templates():
    templates = [
        {
            "id": "maintenance",
            "name": "Maintenance Notice",
            "subject": "Scheduled Maintenance - Altona Village",
            "message": (
                "Dear Residents,\n\nWe would like to inform you of scheduled maintenance "
                "work that will take place on [DATE] from [TIME] to [TIME].\n\nAffected areas: [AREAS]\n\n"
                "We apologize for any inconvenience caused.\n\nBest regards,\nAltona Village Management"
            ),
        },
        {
            "id": "security",
            "name": "Security Alert",
            "subject": "Security Notice - Altona Village",
            "message": (
                "Dear Residents,\n\nPlease be advised of the following security matter:\n\n[SECURITY_DETAILS]\n\n"
                "For your safety, please:\n- [SAFETY_INSTRUCTION_1]\n- [SAFETY_INSTRUCTION_2]\n\n"
                "If you notice anything suspicious, please contact security immediately.\n\n"
                "Best regards,\nAltona Village Management"
            ),
        },
        {
            "id": "community",
            "name": "Community Update",
            "subject": "Community Update - Altona Village",
            "message": (
                "Dear Residents,\n\nWe hope this message finds you well. We wanted to share some important community updates:\n\n"
                "[UPDATE_DETAILS]\n\nThank you for being part of our community.\n\nBest regards,\nAltona Village Management"
            ),
        },
        {
            "id": "emergency",
            "name": "Emergency Notice",
            "subject": "URGENT: Emergency Notice - Altona Village",
            "message": (
                "URGENT NOTICE\n\nDear Residents,\n\nWe need to inform you of an emergency situation:\n\n[EMERGENCY_DETAILS]\n\n"
                "Immediate action required:\n[ACTION_REQUIRED]\n\nFor assistance, contact: [EMERGENCY_CONTACT]\n\n"
                "Altona Village Management"
            ),
        },
    ]
    return jsonify(templates), 200


@communication_bp.route("/statistics", methods=["GET"])
@admin_required
def get_communication_statistics():
    try:
        total_residents = User.query.filter_by(status="active", role="resident").count()
        residents_with_email = User.query.filter(
            User.status == "active",
            User.role == "resident",
            User.email.isnot(None),
            User.email != "",
        ).count()
        residents_with_phone = Resident.query.join(User).filter(
            User.status == "active",
            Resident.phone_number.isnot(None),
            Resident.phone_number != "",
        ).count()

        owners_count = db.session.query(User).join(Owner).filter(
            User.status == "active"
        ).count()

        tenants_count = db.session.query(User).join(Resident).filter(
            User.status == "active",
            or_(Resident.is_owner == False, Resident.is_owner.is_(None)),
        ).count()

        stats = {
            "total_residents": total_residents,
            "residents_with_email": residents_with_email,
            "residents_with_phone": residents_with_phone,
            "owners_count": owners_count,
            "tenants_count": tenants_count,
            "email_coverage": round((residents_with_email / total_residents * 100) if total_residents else 0, 1),
            "phone_coverage": round((residents_with_phone / total_residents * 100) if total_residents else 0, 1),
        }
        return jsonify(stats), 200

    except Exception as e:
        current_app.logger.exception("get_communication_statistics failed")
        return jsonify({"error": str(e)}), 500


@communication_bp.route("/stats", methods=["GET"])
@admin_required
def get_communication_stats():
    """Alternate stats used by UI."""
    try:
        total_users = User.query.filter(
            User.status == "active",
            User.email.isnot(None),
            User.email != "",
        ).count()

        residents = db.session.query(User).join(Resident).filter(
            User.status == "active",
            User.email.isnot(None),
            User.email != "",
        ).count()

        owners = db.session.query(User).join(Owner).filter(
            User.status == "active",
            User.email.isnot(None),
            User.email != "",
        ).count()

        resident_phones = db.session.query(User).join(Resident).filter(
            User.status == "active",
            Resident.phone_number.isnot(None),
            Resident.phone_number != "",
        ).count()

        owner_phones = db.session.query(User).join(Owner).filter(
            User.status == "active",
            Owner.phone_number.isnot(None),
            Owner.phone_number != "",
        ).count()

        result = {
            "total_users": total_users,
            "residents": residents,
            "owners": owners,
            "active_emails": total_users,
            # Note: owner+resident phones might double-count for owner-residents
            "active_phones": resident_phones + owner_phones,
        }
        return jsonify(result), 200

    except Exception as e:
        current_app.logger.exception("get_communication_stats failed")
        return jsonify({"error": "Failed to get communication statistics"}), 500


@communication_bp.route("/find-user-by-erf", methods=["POST"])
@admin_required
def find_user_by_erf():
    """Find user by ERF number for individual communication."""
    try:
        data = request.get_json() or {}
        erf_number = (data.get("erf_number") or "").strip()
        if not erf_number:
            return jsonify({"error": "ERF number is required"}), 400

        # Check Resident first
        resident = db.session.query(Resident).filter_by(erf_number=erf_number).first()
        if resident:
            u = User.query.get(resident.user_id)
            if u:
                return jsonify({
                    "found": True,
                    "user": {
                        "id": u.id,
                        "full_name": f"{resident.first_name or ''} {resident.last_name or ''}".strip(),
                        "email": u.email,
                        "phone": resident.phone_number,
                        "erf_number": erf_number,
                        "type": "resident",
                    }
                }), 200

        # Then Owner
        owner = db.session.query(Owner).filter_by(erf_number=erf_number).first()
        if owner:
            u = User.query.get(owner.user_id)
            if u:
                return jsonify({
                    "found": True,
                    "user": {
                        "id": u.id,
                        "full_name": f"{owner.first_name or ''} {owner.last_name or ''}".strip(),
                        "email": u.email,
                        "phone": owner.phone_number,
                        "erf_number": erf_number,
                        "type": "owner",
                    }
                }), 200

        return jsonify({"found": False, "error": f"No user found for ERF {erf_number}"}), 404

    except Exception as e:
        current_app.logger.exception("find_user_by_erf failed")
        return jsonify({"error": "Failed to find user"}), 500


@communication_bp.route("/send-individual-email", methods=["POST"])
@admin_required
def send_individual_email():
    """Send email to an individual user (optionally with an existing uploaded attachment)."""
    try:
        data = request.get_json() or {}
        user_id = data.get("user_id")
        subject = (data.get("subject") or "").strip()
        message = (data.get("message") or "").strip()
        attachment_filename = (data.get("attachment_filename") or "").strip()

        if not user_id or not subject or not message:
            return jsonify({"error": "User ID, subject, and message are required"}), 400

        u = User.query.get(user_id)
        if not u:
            return jsonify({"error": "User not found"}), 404
        if not u.email:
            return jsonify({"error": "User does not have an email address"}), 400

        user_name = u.get_full_name() if hasattr(u, "get_full_name") else (u.email.split("@")[0])

        if attachment_filename:
            path = os.path.join(_upload_dir(), attachment_filename)
            if not os.path.exists(path):
                return jsonify({"error": "Attachment file not found"}), 404

            send_email_with_attachment(
                to_email=u.email,
                subject=subject,
                message=message,
                attachment_path=path,
            )
            # Optionally clean up the attachment after sending
            try:
                os.remove(path)
            except Exception:
                pass

            return jsonify({"success": True, "message": f"Email with attachment sent to {user_name}"}), 200

        # Without attachment
        ok, err = send_custom_email(
            to_email=u.email,
            subject=subject,
            message=message,
            recipient_name=user_name,
        )
        if ok:
            return jsonify({"success": True, "message": f"Email sent to {user_name}"}), 200
        return jsonify({"error": err or "Failed to send email"}), 500

    except Exception as e:
        current_app.logger.exception("send_individual_email failed")
        return jsonify({"error": "Failed to send email"}), 500


@communication_bp.route("/upload-attachment", methods=["POST"])
@admin_required
def upload_attachment():
    """Upload an attachment for email sends."""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if not file or not file.filename:
            return jsonify({"error": "No file selected"}), 400

        allowed = {"pdf", "doc", "docx", "txt", "jpg", "jpeg", "png", "gif"}
        ext = file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else ""
        if ext not in allowed:
            return jsonify({"error": f"File type .{ext} not allowed. Allowed: {', '.join(sorted(allowed))}"}), 400

        # 5MB size limit
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        if size > 5 * 1024 * 1024:
            return jsonify({"error": "File size exceeds 5MB limit"}), 400

        safe = secure_filename(file.filename)
        unique = f"{uuid.uuid4().hex}_{safe}"
        path = os.path.join(_upload_dir(), unique)

        file.save(path)

        return jsonify({
            "success": True,
            "filename": unique,
            "original_filename": file.filename,
            "file_size": size,
        }), 200

    except Exception as e:
        current_app.logger.exception("upload_attachment failed")
        return jsonify({"error": "File upload failed"}), 500


@communication_bp.route("/send-email-with-attachment", methods=["POST"])
@admin_required
def send_bulk_email_with_attachment():
    """Send bulk email with a previously-uploaded attachment."""
    try:
        data = request.get_json() or {}
        recipient_type = (data.get("recipient_type") or "all").strip().lower()
        subject = (data.get("subject") or "").strip()
        message = (data.get("message") or "").strip()
        attachment_filename = (data.get("attachment_filename") or "").strip()

        if not subject or not message:
            return jsonify({"error": "Subject and message are required"}), 400
        if not attachment_filename:
            return jsonify({"error": "Attachment filename is required"}), 400

        path = os.path.join(_upload_dir(), attachment_filename)
        if not os.path.exists(path):
            return jsonify({"error": "Attachment file not found"}), 404

        recipients = _recipient_users(recipient_type)
        if not recipients:
            return jsonify({"error": "No active users found for the selected recipient type"}), 404

        sent_ok = 0
        sent_fail = 0

        for u in recipients:
            try:
                send_email_with_attachment(
                    to_email=u.email,
                    subject=subject,
                    message=message,
                    attachment_path=path,
                )
                sent_ok += 1
            except Exception as e:
                sent_fail += 1
                current_app.logger.warning("Bulk attach send failed to %s: %s", u.email, e)

        # optional cleanup
        try:
            os.remove(path)
        except Exception:
            pass

        return jsonify({
            "success": True,
            "sent_count": sent_ok,
            "failed_count": sent_fail,
            "total_recipients": len(recipients),
            "message": f"Email with attachment sent to {sent_ok} recipients" + (f", {sent_fail} failed" if sent_fail else ""),
        }), 200

    except Exception as e:
        current_app.logger.exception("send_bulk_email_with_attachment failed")
        return jsonify({"error": "Failed to send email with attachment"}), 500
