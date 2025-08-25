# src/routes/transition_requests.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date
from werkzeug.security import generate_password_hash

# Models (absolute imports to avoid path issues)
from src.models.user import (
    db, User, Resident, Owner, UserTransitionRequest,
    TransitionRequestUpdate, TransitionVehicle, Vehicle
)

# Same-package import for notifications (lazy side-effects kept out of module import)
from .admin_notifications import log_user_change

# One blueprint; main.py should register at url_prefix="/api/transition"
transition_bp = Blueprint("transition", __name__)


# ------------------------ helpers ------------------------

def _require_admin():
    u = User.query.get(get_jwt_identity())
    if not u or u.role != "admin":
        return None, (jsonify({"error": "Admin access required"}), 403)
    return u, None

def _safe_bool(v):
    return bool(v) if isinstance(v, bool) else str(v).lower() in {"1", "true", "yes", "on"}

def _role_label(resident: bool, owner: bool) -> str:
    if resident and owner:
        return "owner-resident"
    if owner:
        return "owner"
    return "resident"

def _log_change(user, erf_number, change_type, field, old_val, new_val):
    try:
        name = "Unknown User"
        if getattr(user, "resident", None):
            name = f"{user.resident.first_name or ''} {user.resident.last_name or ''}".strip() or name
        elif getattr(user, "owner", None):
            name = f"{user.owner.first_name or ''} {user.owner.last_name or ''}".strip() or name
        log_user_change(
            user_id=user.id,
            user_name=name,
            erf_number=erf_number,
            change_type=change_type,
            field_name=field,
            old_value=str(old_val) if old_val is not None else "",
            new_value=str(new_val) if new_val is not None else "",
        )
    except Exception as e:
        current_app.logger.warning(f"log_user_change failed ({change_type}/{field}): {e}")


# ---------------- link two existing requests (admin) ----------------

@transition_bp.route("/admin/link-existing-requests", methods=["POST"])
@jwt_required()
def link_existing_transition_requests():
    """Link two existing transition requests for the same ERF (owner and tenant) and process migration."""
    _, err = _require_admin()
    if err: return err

    data = request.get_json() or {}
    owner_request_id = data.get("owner_request_id")
    tenant_request_id = data.get("tenant_request_id")

    if not owner_request_id or not tenant_request_id:
        return jsonify({"error": "Both request IDs are required"}), 400

    owner_req  = UserTransitionRequest.query.get(owner_request_id)
    tenant_req = UserTransitionRequest.query.get(tenant_request_id)
    if not owner_req or not tenant_req:
        return jsonify({"error": "One or both transition requests not found"}), 404

    if owner_req.erf_number != tenant_req.erf_number:
        return jsonify({"error": "Transition requests are for different ERFs"}), 400
    if owner_req.status == "completed" or tenant_req.status == "completed":
        return jsonify({"error": "One or both transition requests are already completed"}), 400

    owner_user  = User.query.get(owner_req.user_id)
    tenant_user = User.query.get(tenant_req.user_id)
    if not owner_user or not tenant_user:
        return jsonify({"error": "One or both users not found"}), 404

    owner_is_owner   = Owner.query.filter_by(user_id=owner_user.id,   erf_number=owner_req.erf_number).first() is not None
    tenant_is_res    = Resident.query.filter_by(user_id=tenant_user.id, erf_number=tenant_req.erf_number).first() is not None
    if not owner_is_owner or not tenant_is_res:
        return jsonify({"error": "Role mismatch: expected owner + resident records for ERF"}), 400

    try:
        # deactivate seller/owner
        owner_user.status = "inactive"
        owner_req.status = "completed"
        owner_req.completed_at = datetime.utcnow()

        # tenant becomes owner-resident
        old_role = tenant_user.role
        tenant_user.role = "owner-resident"
        tenant_req.status = "completed"
        tenant_req.completed_at = datetime.utcnow()

        # remove old owner record
        Owner.query.filter_by(user_id=owner_user.id, erf_number=owner_req.erf_number).delete()

        # add owner record for tenant (if not present)
        if not tenant_user.owner:
            db.session.add(Owner(
                user_id=tenant_user.id,
                erf_number=tenant_req.erf_number,
                first_name=getattr(tenant_user.resident, "first_name", "") or "",
                last_name=getattr(tenant_user.resident, "last_name", "") or "",
                phone_number=getattr(tenant_user.resident, "phone_number", "") or ""
            ))

        # ensure resident exists & active
        if tenant_user.resident:
            tenant_user.resident.status = "active"
        else:
            db.session.add(Resident(
                user_id=tenant_user.id,
                erf_number=tenant_req.erf_number,
                first_name="",
                last_name="",
                phone_number="",
                id_number="999999999",
                street_number="1",
                street_name="Main Street",
                full_address=f"{tenant_req.erf_number} Main Street",
                intercom_code="ADMIN_SET_REQUIRED",
                status="active",
            ))

        _log_change(tenant_user, tenant_req.erf_number, "transition_link", "user.role", old_role, tenant_user.role)
        _log_change(owner_user, owner_req.erf_number, "transition_link", "user.status", "active", "inactive")

        db.session.commit()
        return jsonify({"success": True, "message": "Linked & migrated successfully."}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Link existing requests failed")
        return jsonify({"error": f"Failed to process migration: {e}"}), 500


# ---------------- core migration helpers (admin/internal) ----------------

def perform_user_migration(tr):
    """
    Migrate user based on legacy 'new_occupant_*' fields.
    Scenarios:
      1) same person role change
      2) partial replacement (existing different user)
      3) complete replacement (create brand new user)
    """
    try:
        if (not tr.new_occupant_type or tr.new_occupant_type == "unknown" or
            not tr.new_occupant_first_name or not tr.new_occupant_last_name):
            return {"success": True, "message": "No new occupant data supplied; skipping migration."}

        current_user = User.query.get(tr.user_id)
        if not current_user:
            return {"success": False, "error": "Current user not found"}

        target_email = tr.new_occupant_email or (
            f"temp_{tr.new_occupant_first_name.lower()}_{tr.new_occupant_last_name.lower()}@altona-village.temp"
        )
        is_same = (current_user.email == target_email)
        existing_target = None if is_same else User.query.filter_by(email=target_email).first()

        if is_same:
            return _handle_role_change(tr, current_user)
        elif existing_target:
            return _handle_partial_replacement(tr, current_user, existing_target)
        else:
            return _handle_complete_replacement(tr, current_user, target_email)

    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": f"Migration failed: {e}"}


def _handle_role_change(tr, user):
    try:
        erf = tr.erf_number
        new_type = tr.new_occupant_type  # resident | owner | owner-resident

        # top-level role
        old_role = user.role
        if new_type in ("resident", "owner", "owner-resident"):
            user.role = new_type

        # resident record
        if new_type in ("resident", "owner-resident"):
            if not user.resident:
                db.session.add(Resident(
                    user_id=user.id,
                    first_name=tr.new_occupant_first_name,
                    last_name=tr.new_occupant_last_name,
                    erf_number=erf,
                    phone_number=tr.new_occupant_phone or "",
                    id_number=tr.new_occupant_id_number or "999999999",
                    street_number=tr.new_occupant_street_number or "1",
                    street_name=tr.new_occupant_street_name or "Main Street",
                    full_address=tr.new_occupant_full_address or f"{erf} Main Street",
                    intercom_code=tr.new_occupant_intercom_code or "ADMIN_SET_REQUIRED",
                    status="active",
                ))
            else:
                user.resident.status = "active"
                user.resident.erf_number = erf
        else:
            if user.resident:
                user.resident.status = "inactive"

        # owner record
        if new_type in ("owner", "owner-resident"):
            if not user.owner:
                db.session.add(Owner(
                    user_id=user.id,
                    first_name=tr.new_occupant_first_name,
                    last_name=tr.new_occupant_last_name,
                    erf_number=erf,
                    phone_number=tr.new_occupant_phone or "",
                    id_number=tr.new_occupant_id_number or "999999999",
                    street_number=tr.new_occupant_street_number or "1",
                    street_name=tr.new_occupant_street_name or "Main Street",
                    full_address=tr.new_occupant_full_address or f"{erf} Main Street",
                    intercom_code=tr.new_occupant_intercom_code or "ADMIN_SET_REQUIRED",
                    title_deed_number=tr.new_occupant_title_deed_number or "T000000",
                    postal_street_number=tr.new_occupant_postal_street_number or "1",
                    postal_street_name=tr.new_occupant_postal_street_name or "Main Street",
                    postal_suburb=tr.new_occupant_postal_suburb or "Suburb",
                    postal_city=tr.new_occupant_postal_city or "City",
                    postal_code=tr.new_occupant_postal_code or "0000",
                    postal_province=tr.new_occupant_postal_province or "Province",
                    full_postal_address=tr.new_occupant_full_postal_address or "1 Main Street, Suburb, City, 0000",
                    status="active",
                ))
            else:
                user.owner.status = "active"
                user.owner.erf_number = erf
        else:
            if user.owner:
                user.owner.status = "inactive"

        _log_change(user, erf, "migration_role_change", "user.role", old_role, user.role)

        tr.migration_completed = True
        tr.migration_date = datetime.utcnow()
        tr.new_user_id = user.id

        db.session.commit()
        return {"success": True, "message": f"Role change to {user.role} for ERF {erf}", "migration_type": "role_change"}
    except Exception as e:
        db.session.rollback()
        raise e


def _handle_partial_replacement(tr, old_user, new_user):
    try:
        erf = tr.erf_number
        new_type = tr.new_occupant_type  # resident | owner | owner-resident
        now = datetime.utcnow()

        # old user loses one role but stays active with the other
        if new_type == "resident":
            # old keeps owner role
            old_user.role = "owner"
            if old_user.resident:
                old_user.resident.status = "deleted_profile"
                old_user.resident.migration_date = now
                old_user.resident.migration_reason = f"Replaced by {new_user.email} via transition {tr.id}"
        elif new_type == "owner":
            # old keeps resident role
            old_user.role = "resident"
            if old_user.owner:
                old_user.owner.status = "deleted_profile"
                old_user.owner.migration_date = now
                old_user.owner.migration_reason = f"Replaced by {new_user.email} via transition {tr.id}"
        else:
            # fallback to complete replacement
            old_user.status = "inactive"
            old_user.password_hash = "DISABLED"
            for rec in (old_user.resident, old_user.owner):
                if rec:
                    rec.status = "deleted_profile"
                    rec.migration_date = now
                    rec.migration_reason = f"Replaced by {new_user.email} via transition {tr.id}"

        # assign new user role records as needed
        want_res = new_type in ("resident", "owner-resident")
        want_own = new_type in ("owner", "owner-resident")

        new_user.role = _role_label(want_res, want_own)

        if want_res and not new_user.resident:
            db.session.add(Resident(
                user_id=new_user.id,
                first_name=tr.new_occupant_first_name,
                last_name=tr.new_occupant_last_name,
                erf_number=erf,
                phone_number=tr.new_occupant_phone or "",
                id_number=tr.new_occupant_id_number or "999999999",
                street_number=tr.new_occupant_street_number or "1",
                street_name=tr.new_occupant_street_name or "Main Street",
                full_address=tr.new_occupant_full_address or f"{erf} Main Street",
                intercom_code=tr.new_occupant_intercom_code or "ADMIN_SET_REQUIRED",
                status="active",
            ))
        if want_own and not new_user.owner:
            db.session.add(Owner(
                user_id=new_user.id,
                first_name=tr.new_occupant_first_name,
                last_name=tr.new_occupant_last_name,
                erf_number=erf,
                phone_number=tr.new_occupant_phone or "",
                id_number=tr.new_occupant_id_number or "999999999",
                street_number=tr.new_occupant_street_number or "1",
                street_name=tr.new_occupant_street_name or "Main Street",
                full_address=tr.new_occupant_full_address or f"{erf} Main Street",
                intercom_code=tr.new_occupant_intercom_code or "ADMIN_SET_REQUIRED",
                title_deed_number=tr.new_occupant_title_deed_number or "T000000",
                postal_street_number=tr.new_occupant_postal_street_number or "1",
                postal_street_name=tr.new_occupant_postal_street_name or "Main Street",
                postal_suburb=tr.new_occupant_postal_suburb or "Suburb",
                postal_city=tr.new_occupant_postal_city or "City",
                postal_code=tr.new_occupant_postal_code or "0000",
                postal_province=tr.new_occupant_postal_province or "Province",
                full_postal_address=tr.new_occupant_full_postal_address or "1 Main Street, Suburb, City, 0000",
                status="active",
            ))

        _log_change(new_user, erf, "migration_partial", "user.role", getattr(new_user, "role", None), new_user.role)

        tr.migration_completed = True
        tr.migration_date = now
        tr.new_user_id = new_user.id

        db.session.commit()
        return {"success": True, "message": f"Partial replacement to {new_user.role} for ERF {erf}",
                "migration_type": "partial_replacement"}
    except Exception as e:
        db.session.rollback()
        raise e


def _handle_complete_replacement(tr, old_user, new_email):
    try:
        erf = tr.erf_number
        now = datetime.utcnow()

        # deactivate old (and mark records)
        old_user.status = "inactive"
        old_user.password_hash = "DISABLED"
        for rec in (old_user.resident, old_user.owner):
            if rec:
                rec.status = "deleted_profile"
                rec.migration_date = now
                rec.migration_reason = f"Replaced by {new_email} via transition {tr.id}"

        # deactivate vehicles
        old_vs = []
        if old_user.resident:
            old_vs += Vehicle.query.filter_by(resident_id=old_user.resident.id).all()
        if old_user.owner:
            old_vs += Vehicle.query.filter_by(owner_id=old_user.owner.id).all()
        for v in old_vs:
            v.status = "inactive"
            v.migration_date = now
            v.migration_reason = f"Owner replaced by {new_email}"

        # create new user
        temp_password = "test"
        new_user = User(
            email=new_email,
            password_hash=generate_password_hash(temp_password),
            role="resident",
            status="active",
        )
        db.session.add(new_user)
        db.session.flush()

        new_type = tr.new_occupant_type  # resident | owner | owner-resident
        want_res = new_type in ("resident", "owner-resident")
        want_own = new_type in ("owner", "owner-resident")
        new_user.role = _role_label(want_res, want_own)

        if want_res:
            db.session.add(Resident(
                user_id=new_user.id,
                first_name=tr.new_occupant_first_name,
                last_name=tr.new_occupant_last_name,
                erf_number=erf,
                phone_number=tr.new_occupant_phone or "",
                id_number=tr.new_occupant_id_number or "999999999",
                street_number=tr.new_occupant_street_number or "1",
                street_name=tr.new_occupant_street_name or "Main Street",
                full_address=tr.new_occupant_full_address or f"{erf} Main Street",
                intercom_code=tr.new_occupant_intercom_code or "ADMIN_SET_REQUIRED",
                status="active",
            ))
        if want_own:
            db.session.add(Owner(
                user_id=new_user.id,
                first_name=tr.new_occupant_first_name,
                last_name=tr.new_occupant_last_name,
                erf_number=erf,
                phone_number=tr.new_occupant_phone or "",
                id_number=tr.new_occupant_id_number or "999999999",
                street_number=tr.new_occupant_street_number or "1",
                street_name=tr.new_occupant_street_name or "Main Street",
                full_address=tr.new_occupant_full_address or f"{erf} Main Street",
                intercom_code=tr.new_occupant_intercom_code or "ADMIN_SET_REQUIRED",
                title_deed_number=tr.new_occupant_title_deed_number or "T000000",
                postal_street_number="1",
                postal_street_name="Main Street",
                postal_suburb="Suburb",
                postal_city="City",
                postal_code="0000",
                postal_province="Province",
                full_postal_address="1 Main Street, Suburb, City, 0000",
                status="active",
            ))

        tr.migration_completed = True
        tr.migration_date = now
        tr.new_user_id = new_user.id

        _log_change(new_user, erf, "migration_complete", "user.role", "pending", new_user.role)

        db.session.commit()
        return {
            "success": True,
            "message": f"Complete replacement; new user {new_email} created (temp password set)",
            "migration_type": "complete_replacement",
            "new_user_id": new_user.id,
            "new_password": temp_password,
        }
    except Exception as e:
        db.session.rollback()
        raise e


# ----------------------- public user endpoints -----------------------

@transition_bp.route("/request", methods=["POST"])
@jwt_required()
def create_transition_request():
    """Create a new user transition request (user)"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json() or {}

        # required
        required = ["erf_number", "request_type", "current_role", "new_occupant_type"]
        for f in required:
            if not data.get(f):
                return jsonify({"error": f"Missing required field: {f}"}), 400

        if data["request_type"] not in ["owner_sale", "tenant_moveout", "owner_moving", "other"]:
            return jsonify({"error": "Invalid request type"}), 400
        if data["new_occupant_type"] not in ["resident", "owner", "owner_resident", "owner-resident", "terminated"]:
            return jsonify({"error": "Invalid future residency status"}), 400
        if data["current_role"] not in ["owner", "tenant", "owner_resident", "owner-resident"]:
            return jsonify({"error": "Invalid current role"}), 400

        # normalise hyphen/underscore
        new_occ = data["new_occupant_type"].replace("_", "-")
        curr_role = data["current_role"].replace("_", "-")

        tr = UserTransitionRequest(
            user_id=current_user_id,
            erf_number=data["erf_number"],
            request_type=data["request_type"],
            current_role=curr_role,
            new_occupant_type=new_occ,
        )

        # dates
        for f in [
            "intended_moveout_date", "property_transfer_date", "new_occupant_movein_date",
            "expected_transfer_date", "lease_end_date", "rental_start_date"
        ]:
            if data.get(f):
                try:
                    setattr(tr, f, datetime.strptime(data[f], "%Y-%m-%d").date())
                except ValueError:
                    return jsonify({"error": f"Invalid date format for {f}. Use YYYY-MM-DD"}), 400

        # text
        for f in [
            "notice_period", "transfer_attorney", "moveout_reason", "moveout_reason_other",
            "property_management_company", "outstanding_matters_other",
            "new_occupant_name", "new_occupant_phone", "new_occupant_email",
            "access_handover_requirements", "property_condition_notes", "community_introduction_needs",
            "new_occupant_first_name", "new_occupant_last_name",
            "new_occupant_street_number", "new_occupant_street_name", "new_occupant_full_address",
            "new_occupant_intercom_code", "new_occupant_title_deed_number",
            "new_occupant_postal_street_number", "new_occupant_postal_street_name", "new_occupant_postal_suburb",
            "new_occupant_postal_city", "new_occupant_postal_code", "new_occupant_postal_province",
            "new_occupant_full_postal_address", "new_occupant_id_number",
        ]:
            if f in data:
                setattr(tr, f, data.get(f))

        # booleans
        for f in [
            "sale_agreement_signed", "new_owner_details_known", "deposit_return_required",
            "new_tenant_selected", "gate_access_transfer", "intercom_access_transfer",
            "vehicle_registration_transfer", "visitor_access_transfer", "community_notifications_transfer",
            "unpaid_levies", "pending_maintenance", "community_violations",
        ]:
            if f in data:
                setattr(tr, f, _safe_bool(data.get(f)))

        # ints
        for f in ["new_occupant_adults", "new_occupant_children", "new_occupant_pets"]:
            if data.get(f) not in (None, ""):
                try:
                    setattr(tr, f, int(data.get(f)))
                except (ValueError, TypeError):
                    setattr(tr, f, 0)

        # priority
        if data.get("intended_moveout_date"):
            moveout = datetime.strptime(data["intended_moveout_date"], "%Y-%m-%d").date()
            days = (moveout - date.today()).days
            tr.priority = "emergency" if days < 7 else ("urgent" if days < 30 else "standard")

        db.session.add(tr)
        db.session.flush()

        # vehicles (optional)
        if isinstance(data.get("vehicles"), list):
            for v in data["vehicles"]:
                if v.get("license_plate"):
                    db.session.add(TransitionVehicle(
                        transition_request_id=tr.id,
                        vehicle_make=v.get("vehicle_make"),
                        vehicle_model=v.get("vehicle_model"),
                        license_plate=v.get("license_plate"),
                        color=v.get("color"),
                    ))

        db.session.add(TransitionRequestUpdate(
            transition_request_id=tr.id,
            user_id=current_user_id,
            update_text=f"Transition request submitted for ERF {tr.erf_number} - {tr.request_type.replace('_', ' ').title()}",
            update_type="comment",
        ))
        db.session.commit()

        return jsonify({
            "message": "Transition request created successfully",
            "request_id": tr.id,
            "status": tr.status,
            "priority": tr.priority,
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("create_transition_request failed")
        return jsonify({"error": "Failed to create transition request"}), 500


@transition_bp.route("/requests", methods=["GET"])
@jwt_required()
def get_user_transition_requests():
    try:
        uid = get_jwt_identity()
        rows = UserTransitionRequest.query.filter_by(user_id=uid).order_by(
            UserTransitionRequest.created_at.desc()
        ).all()
        return jsonify({"requests": [r.to_dict() for r in rows]}), 200
    except Exception as e:
        current_app.logger.exception("get_user_transition_requests failed")
        return jsonify({"error": "Failed to fetch requests"}), 500


@transition_bp.route("/request/<request_id>", methods=["GET"])
@jwt_required()
def get_transition_request(request_id):
    try:
        current_user = User.query.get(get_jwt_identity())
        tr = UserTransitionRequest.query.get_or_404(request_id)
        if tr.user_id != current_user.id and current_user.role != "admin":
            return jsonify({"error": "Access denied"}), 403

        payload = tr.to_dict()
        updates = TransitionRequestUpdate.query.filter_by(
            transition_request_id=request_id
        ).order_by(TransitionRequestUpdate.created_at.desc()).all()
        vehicles = TransitionVehicle.query.filter_by(transition_request_id=request_id).all()
        payload["updates"] = [u.to_dict() for u in updates]
        payload["vehicles"] = [v.to_dict() for v in vehicles]
        return jsonify(payload), 200
    except Exception as e:
        current_app.logger.exception("get_transition_request failed")
        return jsonify({"error": "Failed to fetch request"}), 500


@transition_bp.route("/request/<request_id>/update", methods=["POST"])
@jwt_required()
def add_transition_request_update(request_id):
    try:
        uid = get_jwt_identity()
        data = request.get_json() or {}
        if not (data.get("update_text") or "").strip():
            return jsonify({"error": "Update text is required"}), 400

        tr = UserTransitionRequest.query.get_or_404(request_id)
        actor = User.query.get(uid)
        if tr.user_id != uid and actor.role != "admin":
            return jsonify({"error": "Access denied"}), 403

        upd = TransitionRequestUpdate(
            transition_request_id=request_id,
            user_id=uid,
            update_text=data["update_text"].strip(),
            update_type=data.get("update_type", "comment"),
        )
        db.session.add(upd)

        tr.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({"message": "Update added successfully", "update": upd.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("add_transition_request_update failed")
        return jsonify({"error": "Failed to add update"}), 500


# -------------------------- admin lists/details --------------------------

@transition_bp.route("/admin/requests", methods=["GET"])
@jwt_required()
def get_all_transition_requests():
    _, err = _require_admin()
    if err: return err
    try:
        q = UserTransitionRequest.query
        status_filter  = request.args.get("status")
        priority_filter = request.args.get("priority")
        erf_filter     = request.args.get("erf_number")

        if status_filter:
            q = q.filter(UserTransitionRequest.status == status_filter)
        if priority_filter:
            q = q.filter(UserTransitionRequest.priority == priority_filter)
        if erf_filter:
            q = q.filter(UserTransitionRequest.erf_number.contains(erf_filter))

        rows = q.order_by(UserTransitionRequest.priority.desc(),
                          UserTransitionRequest.created_at.desc()).all()
        return jsonify({"requests": [r.to_dict() for r in rows], "total": len(rows)}), 200
    except Exception as e:
        current_app.logger.exception("get_all_transition_requests failed")
        return jsonify({"error": "Failed to fetch requests"}), 500


@transition_bp.route("/admin/request/<request_id>", methods=["GET"])
@jwt_required()
def get_admin_transition_request_details(request_id):
    _, err = _require_admin()
    if err: return err
    try:
        tr = UserTransitionRequest.query.filter_by(id=request_id).first()
        if not tr:
            return jsonify({"error": "Request not found"}), 404

        updates = TransitionRequestUpdate.query.filter_by(
            transition_request_id=request_id
        ).order_by(TransitionRequestUpdate.created_at.desc()).all()
        vehicles = TransitionVehicle.query.filter_by(transition_request_id=request_id).all()

        payload = tr.to_dict()
        payload["updates"]  = [u.to_dict() for u in updates]
        payload["vehicles"] = [v.to_dict() for v in vehicles]
        return jsonify(payload), 200
    except Exception as e:
        current_app.logger.exception("get_admin_transition_request_details failed")
        return jsonify({"error": "Failed to fetch request details"}), 500


@transition_bp.route("/admin/request/<request_id>/assign", methods=["PUT"])
@jwt_required()
def assign_transition_request(request_id):
    admin, err = _require_admin()
    if err: return err
    try:
        tr = UserTransitionRequest.query.get_or_404(request_id)
        data = request.get_json() or {}
        admin_id = data.get("admin_id", admin.id)

        assignee = User.query.get(admin_id)
        if not assignee or assignee.role != "admin":
            return jsonify({"error": "Invalid admin ID"}), 400

        old_admin_id = tr.assigned_admin
        tr.assigned_admin = admin_id
        tr.updated_at = datetime.utcnow()

        if old_admin_id:
            old_admin = User.query.get(old_admin_id)
            note = f"Request reassigned from {old_admin.get_full_name() if old_admin else 'Unknown'} to {assignee.get_full_name()}"
        else:
            note = f"Request assigned to {assignee.get_full_name()}"

        db.session.add(TransitionRequestUpdate(
            transition_request_id=request_id,
            user_id=admin.id,
            update_text=note,
            update_type="admin_note",
        ))
        db.session.commit()

        return jsonify({"message": "Request assigned", "assigned_to": assignee.get_full_name()}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("assign_transition_request failed")
        return jsonify({"error": "Failed to assign request"}), 500


@transition_bp.route("/admin/request/<request_id>/status", methods=["PUT"])
@jwt_required()
def update_transition_request_status(request_id):
    _, err = _require_admin()
    if err: return err
    try:
        tr = UserTransitionRequest.query.get_or_404(request_id)
        data = request.get_json() or {}

        new_status = data.get("status")
        admin_notes = data.get("admin_notes")

        valid = ["pending_review", "in_progress", "awaiting_docs", "ready_for_transition", "completed", "cancelled"]
        if new_status not in valid:
            return jsonify({"error": "Invalid status"}), 400

        old_status = tr.status
        tr.status = new_status
        tr.updated_at = datetime.utcnow()
        if admin_notes:
            tr.admin_notes = admin_notes

        if new_status == "completed":
            tr.completion_date = datetime.utcnow()

            is_termination = (
                tr.new_occupant_type == "terminated" or
                tr.request_type == "exit" or
                (tr.new_occupant_type in ["", "unknown", None] and not tr.new_occupant_first_name)
            )
            privacy_compliant = (
                not tr.new_occupant_first_name or
                not tr.new_occupant_last_name or
                not tr.new_occupant_type or
                tr.new_occupant_type in ["", "unknown", None]
            )

            if is_termination:
                if not tr.migration_completed:
                    pending_user = _find_pending_user_for_erf(tr.erf_number)
                    if pending_user:
                        return jsonify({"error": f"Pending user exists for ERF {tr.erf_number}. Use Transition Linking."}), 400
                    result = _handle_termination(tr)
                    if not result["success"]:
                        return jsonify({"error": f"Termination failed: {result['error']}"}), 500
                    tr.migration_completed = True

            elif privacy_compliant:
                if not tr.migration_completed:
                    return jsonify({"error": "Privacy-compliant requests must be completed via Transition Linking."}), 400
            else:
                result = perform_user_migration(tr)
                if not result["success"]:
                    return jsonify({"error": f"Migration failed: {result['error']}"}), 500

        db.session.add(TransitionRequestUpdate(
            transition_request_id=request_id,
            user_id=get_jwt_identity(),
            update_text=data.get("update_message", f"Status changed from {old_status} to {new_status}"),
            update_type="status_change",
            old_status=old_status,
            new_status=new_status,
        ))
        db.session.commit()

        return jsonify({"message": "Status updated", "old_status": old_status, "new_status": new_status}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("update_transition_request_status failed")
        return jsonify({"error": "Failed to update status"}), 500


@transition_bp.route("/stats", methods=["GET"])
@jwt_required()
def get_transition_stats():
    _, err = _require_admin()
    if err: return err
    try:
        status_counts = {s: UserTransitionRequest.query.filter_by(status=s).count()
                         for s in ["pending_review", "in_progress", "awaiting_docs", "ready_for_transition", "completed", "cancelled"]}

        priority_counts = {p: UserTransitionRequest.query.filter_by(priority=p).count()
                           for p in ["standard", "urgent", "emergency"]}

        type_counts = {t: UserTransitionRequest.query.filter_by(request_type=t).count()
                       for t in ["owner_sale", "tenant_moveout", "owner_moving", "other"]}

        return jsonify({
            "status_counts": status_counts,
            "priority_counts": priority_counts,
            "type_counts": type_counts,
            "total_requests": UserTransitionRequest.query.count(),
        }), 200
    except Exception as e:
        current_app.logger.exception("get_transition_stats failed")
        return jsonify({"error": "Failed to fetch statistics"}), 500


# -------------------- linking with pending registration (admin) --------------------

@transition_bp.route("/admin/link-and-process", methods=["POST"])
@jwt_required()
def link_and_process_transition():
    admin, err = _require_admin()
    if err: return err
    try:
        data = request.get_json() or {}
        transition_request_id = data.get("transition_request_id")
        registration_id = data.get("registration_id")
        new_user_data = data.get("new_user_data")
        if not all([transition_request_id, registration_id, new_user_data]):
            return jsonify({"error": "Missing required data"}), 400

        tr = UserTransitionRequest.query.get(transition_request_id)
        if not tr:
            return jsonify({"error": "Transition request not found"}), 404

        pending = User.query.filter_by(id=registration_id, status="pending").first()
        if not pending:
            return jsonify({"error": "Pending registration not found"}), 404

        # ERF match
        pending_erf = None
        if pending.resident:
            pending_erf = pending.resident.erf_number
        elif pending.owner:
            pending_erf = pending.owner.erf_number
        if tr.erf_number != pending_erf:
            return jsonify({"error": f"ERF mismatch: request {tr.erf_number} vs registration {pending_erf}"}), 400

        old_user = User.query.get(tr.user_id)
        if not old_user:
            return jsonify({"error": "Current user not found"}), 404

        result = _perform_linked_migration(tr, old_user, pending, new_user_data)
        if not result["success"]:
            return jsonify({"error": result["error"]}), 500

        # finalize
        tr.status = "completed"
        tr.migration_completed = True
        tr.migration_date = datetime.utcnow()
        tr.new_user_id = pending.id

        db.session.add(TransitionRequestUpdate(
            transition_request_id=tr.id,
            user_id=admin.id,
            update_text=f"Transition completed by linking with registration {registration_id}. {result['message']}",
            update_type="admin_note",
            old_status="in_progress",
            new_status="completed",
        ))
        db.session.commit()

        return jsonify({
            "message": "Transition processed successfully",
            "transition_id": tr.id,
            "new_user_id": pending.id,
            "migration_type": result.get("migration_type", "linked_replacement"),
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("link_and_process_transition failed")
        return jsonify({"error": f"Failed to process transition: {e}"}), 500


def _perform_linked_migration(tr, old_user, new_user, new_user_data):
    try:
        erf = tr.erf_number
        now = datetime.utcnow()
        mig_reason = f"Linked transition {tr.id} with {new_user.email}"

        # what old user currently has
        old_has_res = bool(old_user.resident and old_user.resident.status == "active")
        old_has_own = bool(old_user.owner and old_user.owner.status == "active")
        old_role = _role_label(old_has_res, old_has_own)

        intended = (tr.new_occupant_type or "").replace("_", "-")
        if intended == "terminated":
            return _handle_termination(tr)

        # infer new desired roles
        if intended == "owner-resident":
            new_res, new_own = True, True
        elif intended == "owner":
            new_res, new_own = False, True
        elif intended == "resident":
            new_res, new_own = True, False
        else:
            new_res = _safe_bool(new_user_data.get("is_resident", False))
            new_own = _safe_bool(new_user_data.get("is_owner", False))

        partial = False
        if old_role == "owner-resident":
            if new_res and not new_own:
                partial = True    # old keeps owner
                old_user.role = "owner"
                if old_user.resident:
                    old_user.resident.status = "deleted_profile"
                    old_user.resident.migration_date = now
                    old_user.resident.migration_reason = mig_reason
            elif new_own and not new_res:
                partial = True    # old keeps resident
                old_user.role = "resident"
                if old_user.owner:
                    old_user.owner.status = "deleted_profile"
                    old_user.owner.migration_date = now
                    old_user.owner.migration_reason = mig_reason
        if not partial:
            # complete replacement
            old_user.status = "inactive"
            old_user.password_hash = "DISABLED"
            for rec in (old_user.resident, old_user.owner):
                if rec:
                    rec.status = "deleted_profile"
                    rec.migration_date = now
                    rec.migration_reason = mig_reason
            old_vs = []
            if old_user.resident:
                old_vs += Vehicle.query.filter_by(resident_id=old_user.resident.id).all()
            if old_user.owner:
                old_vs += Vehicle.query.filter_by(owner_id=old_user.owner.id).all()
            for v in old_vs:
                v.status = "inactive"
                v.migration_date = now
                v.migration_reason = mig_reason

        # activate new user + ensure role records
        new_user.status = "active"
        new_user.role = _role_label(new_res, new_own)

        if new_res:
            if new_user.resident:
                new_user.resident.status = "active"
                new_user.resident.erf_number = erf
                new_user.resident.intercom_code = "ADMIN_SET_REQUIRED"
            else:
                db.session.add(Resident(
                    user_id=new_user.id,
                    first_name=new_user_data.get("first_name", ""),
                    last_name=new_user_data.get("last_name", ""),
                    erf_number=erf,
                    phone_number=new_user_data.get("phone_number", ""),
                    id_number=new_user_data.get("id_number", "999999999"),
                    street_number="1",
                    street_name="Main Street",
                    full_address=new_user_data.get("address", f"{erf} Main Street"),
                    intercom_code="ADMIN_SET_REQUIRED",
                    status="active",
                ))
        if new_own:
            if new_user.owner:
                new_user.owner.status = "active"
                new_user.owner.erf_number = erf
                new_user.owner.intercom_code = "ADMIN_SET_REQUIRED"
            else:
                db.session.add(Owner(
                    user_id=new_user.id,
                    first_name=new_user_data.get("first_name", ""),
                    last_name=new_user_data.get("last_name", ""),
                    erf_number=erf,
                    phone_number=new_user_data.get("phone_number", ""),
                    id_number=new_user_data.get("id_number", "999999999"),
                    street_number="1",
                    street_name="Main Street",
                    full_address=new_user_data.get("address", f"{erf} Main Street"),
                    intercom_code="ADMIN_SET_REQUIRED",
                    title_deed_number="T000000",
                    postal_street_number="1",
                    postal_street_name="Main Street",
                    postal_suburb="Suburb",
                    postal_city="City",
                    postal_code="0000",
                    postal_province="Province",
                    full_postal_address="1 Main Street, Suburb, City, 0000",
                    status="active",
                ))

        tr.migration_completed = True
        tr.migration_date = now
        tr.new_user_id = new_user.id
        tr.status = "completed"

        db.session.commit()
        return {
            "success": True,
            "message": f"Migrated ERF {erf}: {old_role} → {new_user.role}",
            "migration_type": "partial_replacement" if partial else "complete_replacement",
        }
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": f"Linked migration failed: {e}"}


@transition_bp.route("/admin/request/<request_id>/mark-migration-completed", methods=["PUT"])
@jwt_required()
def mark_transition_migration_completed(request_id):
    _, err = _require_admin()
    if err: return err
    try:
        tr = UserTransitionRequest.query.get_or_404(request_id)
        tr.migration_completed = True
        tr.migration_date = datetime.utcnow()
        tr.updated_at = datetime.utcnow()

        db.session.add(TransitionRequestUpdate(
            transition_request_id=request_id,
            user_id=get_jwt_identity(),
            update_text="Migration manually marked as completed after successful transition linking",
            update_type="admin_note",
        ))
        db.session.commit()

        return jsonify({
            "message": "Transition request marked as migration completed",
            "migration_completed": True,
            "migration_date": tr.migration_date.isoformat(),
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("mark_transition_migration_completed failed")
        return jsonify({"error": "Failed to mark migration as completed"}), 500


# ----------------------- termination helper -----------------------

def _handle_termination(tr):
    try:
        user = User.query.get(tr.user_id)
        if not user:
            return {"success": False, "error": "User not found"}

        erf = tr.erf_number
        user.status = "inactive"

        if user.resident:
            user.resident.status = "inactive"
            user.resident.migration_date = datetime.utcnow()
            user.resident.migration_reason = f"User terminated from ERF {erf}"
        if user.owner:
            user.owner.status = "inactive"
            user.owner.migration_date = datetime.utcnow()
            user.owner.migration_reason = f"User terminated from ERF {erf}"

        vehicles = []
        if user.resident:
            vehicles += Vehicle.query.filter_by(resident_id=user.resident.id).all()
        if user.owner:
            vehicles += Vehicle.query.filter_by(owner_id=user.owner.id).all()
        for v in vehicles:
            v.status = "terminated"
            v.migration_date = datetime.utcnow()
            v.migration_reason = f"User terminated from ERF {erf}"

        _log_change(user, erf, "transition_termination", "user.status", "active", "terminated")

        tr.migration_completed = True
        tr.migration_date = datetime.utcnow()

        db.session.add(TransitionRequestUpdate(
            transition_request_id=tr.id,
            user_id=tr.user_id,
            update_text=f"User terminated and removed from ERF {erf}. All access revoked.",
            update_type="termination",
        ))
        db.session.commit()

        return {"success": True, "message": f"User terminated for ERF {erf}", "user_id": user.id, "erf_number": erf}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("_handle_termination failed")
        return {"success": False, "error": f"Termination failed: {e}"}


def _find_pending_user_for_erf(erf_number):
    try:
        for r in Resident.query.filter_by(erf_number=erf_number).all():
            if r.user and r.user.status == "pending":
                return r.user
        for o in Owner.query.filter_by(erf_number=erf_number).all():
            if o.user and o.user.status == "pending":
                return o.user
        return None
    except Exception as e:
        current_app.logger.warning(f"_find_pending_user_for_erf error: {e}")
        return None
