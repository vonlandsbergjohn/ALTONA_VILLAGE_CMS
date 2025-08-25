# altona_village_cms/src/routes/transition_linking.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from src.models.user import db, User, Resident, Owner
from src.models.user import UserTransitionRequest  # keep this import as in your project

# best-effort change logger (does nothing if not available)
try:
    from src.routes.admin_notifications import log_user_change
except Exception:
    def log_user_change(*args, **kwargs):
        pass

transition_linking_bp = Blueprint("transition_linking", __name__)

# ----------------------------- helpers --------------------------------

def admin_required(fn):
    from functools import wraps
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        uid = get_jwt_identity()
        user = User.query.get(uid)
        if not user or user.role != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper


def _user_name_and_erf_for(user: User, erf_number: str):
    """
    Get display name and erf for a user at a specific ERF, preferring Resident, then Owner.
    """
    name = user.email or "User"
    erf = erf_number

    # Prefer resident record at this ERF
    r = None
    if user.resident and getattr(user.resident, "erf_number", None) == erf_number:
        r = user.resident
    # else check owner record
    o = None
    if user.owner and getattr(user.owner, "erf_number", None) == erf_number:
        o = user.owner

    if r:
        fn = (r.first_name or "").strip()
        ln = (r.last_name or "").strip()
        full = f"{fn} {ln}".strip()
        if full:
            name = full
    elif o:
        fn = (o.first_name or "").strip()
        ln = (o.last_name or "").strip()
        full = f"{fn} {ln}".strip()
        if full:
            name = full

    return name, erf

# ------------------------------ route ---------------------------------

@transition_linking_bp.route("/admin/link-existing-requests", methods=["POST"])
@admin_required
def link_existing_transition_requests():
    """
    Link two existing transition requests (owner & tenant) for the same ERF,
    process the property migration, and update statuses.

    Effects:
      - Old owner (seller) user.status -> 'inactive'
      - Delete Owner row for seller at that ERF
      - Tenant becomes 'owner-resident':
          * keep existing Resident row
          * create Owner row for that ERF (if missing)
      - Both requests marked 'completed'
      - Key changes are logged via log_user_change()
    """
    data = request.get_json() or {}
    owner_request_id = data.get("owner_request_id")
    tenant_request_id = data.get("tenant_request_id")

    if not owner_request_id or not tenant_request_id:
        return jsonify({"error": "Both request IDs are required"}), 400

    owner_req = UserTransitionRequest.query.get(owner_request_id)
    tenant_req = UserTransitionRequest.query.get(tenant_request_id)

    if not owner_req or not tenant_req:
        return jsonify({"error": "One or both transition requests not found"}), 404

    # Must be the same ERF and not yet completed
    if owner_req.erf_number != tenant_req.erf_number:
        return jsonify({"error": "Transition requests are for different ERFs"}), 400
    if owner_req.status == "completed" or tenant_req.status == "completed":
        return jsonify({"error": "One or both transition requests are already completed"}), 400

    erf = owner_req.erf_number

    old_owner_user = User.query.get(owner_req.user_id)
    new_owner_user = User.query.get(tenant_req.user_id)
    if not old_owner_user or not new_owner_user:
        return jsonify({"error": "One or both users not found"}), 404

    # Validate roles at that ERF:
    # old owner must have an Owner row for that ERF
    old_owner_row = Owner.query.filter_by(user_id=old_owner_user.id, erf_number=erf).first()
    # new owner must have a Resident row for that ERF
    new_resident_row = Resident.query.filter_by(user_id=new_owner_user.id, erf_number=erf).first()

    if not old_owner_row or not new_resident_row:
        return jsonify({"error": "Role mismatch: expected an Owner for seller and a Resident for buyer at this ERF"}), 400

    try:
        # ----- Deactivate the seller -----
        if old_owner_user.status != "inactive":
            old_name, _ = _user_name_and_erf_for(old_owner_user, erf)
            log_user_change(
                user_id=old_owner_user.id,
                user_name=old_name,
                erf_number=erf,
                change_type="transition",
                field_name="status",
                old_value=old_owner_user.status,
                new_value="inactive",
            )
            old_owner_user.status = "inactive"

        # Remove seller's Owner row for this ERF
        db.session.delete(old_owner_row)

        # ----- Promote tenant to owner-resident -----
        # Ensure an Owner row exists for the new owner at this ERF
        new_owner_row = Owner.query.filter_by(user_id=new_owner_user.id, erf_number=erf).first()
        if not new_owner_row:
            # Populate minimal fields from resident row (names/phone/address fields as available)
            new_owner_row = Owner(
                user_id=new_owner_user.id,
                erf_number=erf,
                first_name=new_resident_row.first_name,
                last_name=new_resident_row.last_name,
                phone_number=getattr(new_resident_row, "phone_number", None),
                street_number=getattr(new_resident_row, "street_number", None),
                street_name=getattr(new_resident_row, "street_name", None),
                full_address=getattr(new_resident_row, "full_address", None),
            )
            db.session.add(new_owner_row)

        # Flip tenant user role -> owner-resident
        if new_owner_user.role != "owner-resident":
            new_name, _ = _user_name_and_erf_for(new_owner_user, erf)
            log_user_change(
                user_id=new_owner_user.id,
                user_name=new_name,
                erf_number=erf,
                change_type="transition",
                field_name="role",
                old_value=new_owner_user.role,
                new_value="owner-resident",
            )
            new_owner_user.role = "owner-resident"

        # Mark resident row as now an owner too (if your schema has this flag)
        if hasattr(new_resident_row, "is_owner") and not new_resident_row.is_owner:
            log_user_change(
                user_id=new_owner_user.id,
                user_name=new_name,
                erf_number=erf,
                change_type="transition",
                field_name="resident.is_owner",
                old_value="False",
                new_value="True",
            )
            new_resident_row.is_owner = True

        # ----- Complete both transition requests -----
        now = datetime.utcnow()
        owner_req.status = "completed"
        owner_req.completed_at = now
        tenant_req.status = "completed"
        tenant_req.completed_at = now

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Transition requests linked and migration processed.",
            "erf_number": erf,
            "old_owner_user_id": old_owner_user.id,
            "new_owner_user_id": new_owner_user.id,
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to process migration: {e}"}), 500
