# src/routes/resident.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from src.models.user import User, Resident, Owner, Vehicle, Complaint, ComplaintUpdate, db

# Import change tracking function (safe fallback if module isn't present)
try:
    from src.routes.admin_notifications import log_user_change
except Exception:
    def log_user_change(*args, **kwargs):
        pass


resident_bp = Blueprint("resident", __name__)


# -------------------------- helpers --------------------------

def get_current_user_data():
    """Return (user, resident_row, owner_row) for the current JWT identity."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return None, None, None

    resident_data = user.resident if user.is_resident() else None
    owner_data = user.owner if user.is_owner() else None
    return user, resident_data, owner_data


def get_current_resident():
    """Legacy helper that returns the resident row when the current user is a resident."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != "resident":
        return None
    return user.resident


def _display_name_and_erf_for(user: User):
    """Convenience: best-effort display name + erf_number for change logging."""
    fn = getattr(user.resident, "first_name", "") or getattr(user.owner, "first_name", "") or ""
    ln = getattr(user.resident, "last_name", "") or getattr(user.owner, "last_name", "") or ""
    name = f"{fn} {ln}".strip() or (user.email or "Unknown User")
    erf = (
        getattr(user.resident, "erf_number", "")
        or getattr(user.owner, "erf_number", "")
        or "Unknown"
    )
    return name, erf


# -------------------------- vehicles --------------------------

@resident_bp.route("/vehicles", methods=["GET"])
@jwt_required()
def get_my_vehicles():
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if not current_user:
            return jsonify({"error": "User not found"}), 404

        # multi-ERF: gather vehicles across all accounts using this email
        all_user_accounts = User.query.filter_by(email=current_user.email).all()

        vehicles = []
        seen_ids = set()

        for acct in all_user_accounts:
            if acct.resident:
                for v in Vehicle.query.filter_by(resident_id=acct.resident.id).all():
                    if v.id in seen_ids:
                        continue
                    d = v.to_dict()
                    d["erf_number"] = acct.resident.erf_number
                    d["property_address"] = acct.resident.full_address or "Address not available"
                    d["user_id"] = acct.id
                    vehicles.append(d)
                    seen_ids.add(v.id)

            if acct.owner:
                for v in Vehicle.query.filter_by(owner_id=acct.owner.id).all():
                    if v.id in seen_ids:
                        continue
                    d = v.to_dict()
                    d["erf_number"] = acct.owner.erf_number
                    d["property_address"] = acct.owner.full_address or "Address not available"
                    d["user_id"] = acct.id
                    vehicles.append(d)
                    seen_ids.add(v.id)

        return jsonify(vehicles), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@resident_bp.route("/vehicles", methods=["POST"])
@jwt_required()
def add_vehicle():
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if not current_user:
            return jsonify({"error": "User not found"}), 404

        data = request.get_json() or {}

        reg = (data.get("registration_number") or "").strip()
        if not reg:
            return jsonify({"error": "registration_number is required"}), 400

        # uniqueness (case-insensitive)
        if db.session.query(Vehicle.id).filter(func.lower(Vehicle.registration_number) == reg.lower()).first():
            return jsonify({"error": "Vehicle with this registration number already exists"}), 400

        # multi-ERF target selection (frontend sends user_id for the chosen ERF)
        all_user_accounts = User.query.filter_by(email=current_user.email).all()
        target_user_id = data.get("erf_selection")
        if target_user_id:
            target_user = next((u for u in all_user_accounts if str(u.id) == str(target_user_id)), None)
            if not target_user:
                return jsonify({"error": "Invalid ERF selection"}), 400
        else:
            target_user = current_user

        target_resident = target_user.resident if target_user.is_resident() else None
        target_owner = target_user.owner if target_user.is_owner() else None
        if not target_resident and not target_owner:
            return jsonify({"error": "Selected ERF has no resident or owner data"}), 400

        vehicle = Vehicle(
            resident_id=target_resident.id if target_resident else None,
            owner_id=(target_owner.id if (target_owner and not target_resident) else None),
            registration_number=reg,
            make=data.get("make"),
            model=data.get("model"),
            color=data.get("color"),
        )
        db.session.add(vehicle)
        db.session.commit()

        # change logging
        try:
            user_name, erf_number = _display_name_and_erf_for(target_user)

            # Critical: the registration number (used by the gate system)
            log_user_change(
                target_user.id,
                user_name,
                erf_number,
                "vehicle_add",
                "vehicle_registration",
                "None",
                reg,
            )

            # Optional non-critical meta:
            if data.get("make"):
                log_user_change(target_user.id, user_name, erf_number, "vehicle_add", "vehicle_make", "None", data["make"])
            if data.get("model"):
                log_user_change(target_user.id, user_name, erf_number, "vehicle_add", "vehicle_model", "None", data["model"])
            if data.get("color"):
                log_user_change(target_user.id, user_name, erf_number, "vehicle_add", "vehicle_color", "None", data["color"])
        except Exception as log_err:
            print(f"[add_vehicle] logging failed: {log_err}")

        return jsonify(vehicle.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@resident_bp.route("/vehicles/<vehicle_id>", methods=["PUT"])
@jwt_required()
def update_vehicle(vehicle_id):
    try:
        user, resident_data, owner_data = get_current_user_data()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # find the vehicle belonging to this user (resident or owner)
        vehicle = None
        if resident_data:
            vehicle = Vehicle.query.filter_by(id=vehicle_id, resident_id=resident_data.id).first()
        if not vehicle and owner_data:
            vehicle = Vehicle.query.filter_by(id=vehicle_id, owner_id=owner_data.id).first()
        if not vehicle:
            return jsonify({"error": "Vehicle not found"}), 404

        data = request.get_json() or {}

        # registration update (critical)
        if "registration_number" in data:
            new_reg = (data["registration_number"] or "").strip()
            if not new_reg:
                return jsonify({"error": "registration_number cannot be empty"}), 400

            # uniqueness (case-insensitive), excluding this record
            existing = (
                Vehicle.query
                .filter(func.lower(Vehicle.registration_number) == new_reg.lower(), Vehicle.id != vehicle.id)
                .first()
            )
            if existing:
                return jsonify({"error": "Vehicle with this registration number already exists"}), 400

            if vehicle.registration_number != new_reg:
                user_name, erf_number = _display_name_and_erf_for(user)
                try:
                    log_user_change(
                        user_id=user.id,
                        user_name=user_name,
                        erf_number=erf_number,
                        change_type="vehicle_update",
                        field_name="vehicle_registration",
                        old_value=vehicle.registration_number or "",
                        new_value=new_reg,
                    )
                except Exception as log_err:
                    print(f"[update_vehicle] reg logging failed: {log_err}")

                vehicle.registration_number = new_reg

        # non-critical meta updates
        for key, field_name in (
            ("make", "vehicle_make"),
            ("model", "vehicle_model"),
            ("color", "vehicle_color"),
        ):
            if key in data and data[key] != getattr(vehicle, key):
                old_val = getattr(vehicle, key)
                setattr(vehicle, key, data[key])
                user_name, erf_number = _display_name_and_erf_for(user)
                try:
                    log_user_change(
                        user_id=user.id,
                        user_name=user_name,
                        erf_number=erf_number,
                        change_type="vehicle_update",
                        field_name=field_name,
                        old_value=str(old_val) if old_val else "",
                        new_value=str(data[key]) if data[key] else "",
                    )
                except Exception as log_err:
                    print(f"[update_vehicle] meta logging failed ({field_name}): {log_err}")

        db.session.commit()
        return jsonify(vehicle.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@resident_bp.route("/vehicles/<vehicle_id>", methods=["DELETE"])
@jwt_required()
def delete_vehicle(vehicle_id):
    try:
        user, resident_data, owner_data = get_current_user_data()
        if not user:
            return jsonify({"error": "User not found"}), 404

        vehicle = None
        if resident_data:
            vehicle = Vehicle.query.filter_by(id=vehicle_id, resident_id=resident_data.id).first()
        if not vehicle and owner_data:
            vehicle = Vehicle.query.filter_by(id=vehicle_id, owner_id=owner_data.id).first()
        if not vehicle:
            return jsonify({"error": "Vehicle not found"}), 404

        old_reg = vehicle.registration_number or ""

        db.session.delete(vehicle)
        db.session.commit()

        # Log as critical so the gate list stays accurate
        try:
            user_name, erf_number = _display_name_and_erf_for(user)
            log_user_change(
                user_id=user.id,
                user_name=user_name,
                erf_number=erf_number,
                change_type="vehicle_delete",
                field_name="vehicle_registration",
                old_value=old_reg,
                new_value="DELETED",
            )
        except Exception as log_err:
            print(f"[delete_vehicle] logging failed: {log_err}")

        return jsonify({"message": "Vehicle deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# -------------------------- complaints (unchanged except minor hygiene) --------------------------

@resident_bp.route("/complaints", methods=["GET"])
@jwt_required()
def get_my_complaints():
    try:
        resident = get_current_resident()
        if not resident:
            return jsonify({"error": "Resident not found"}), 404

        complaints = []
        for c in resident.complaints:
            c_data = c.to_dict()
            if c.updates:
                updates_with_user = []
                for u in c.updates:
                    u_data = u.to_dict()
                    update_user = User.query.get(u.user_id)
                    if update_user:
                        u_data["admin_name"] = update_user.get_full_name()
                        u_data["admin_role"] = update_user.role
                    updates_with_user.append(u_data)
                c_data["updates"] = updates_with_user
            complaints.append(c_data)

        return jsonify(complaints), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@resident_bp.route("/complaints", methods=["POST"])
@jwt_required()
def submit_complaint():
    try:
        resident = get_current_resident()
        if not resident:
            return jsonify({"error": "Resident not found"}), 404

        data = request.get_json() or {}
        complaint = Complaint(
            resident_id=resident.id,
            subject=data.get("subject", "").strip(),
            description=data.get("description", "").strip(),
            priority=data.get("priority", "medium"),
        )
        db.session.add(complaint)
        db.session.commit()
        return jsonify(complaint.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@resident_bp.route("/complaints/<complaint_id>", methods=["GET"])
@jwt_required()
def get_complaint(complaint_id):
    try:
        resident = get_current_resident()
        if not resident:
            return jsonify({"error": "Resident not found"}), 404

        complaint = Complaint.query.filter_by(id=complaint_id, resident_id=resident.id).first()
        if not complaint:
            return jsonify({"error": "Complaint not found"}), 404

        data = complaint.to_dict()
        if complaint.updates:
            updates_with_user = []
            for u in complaint.updates:
                u_data = u.to_dict()
                update_user = User.query.get(u.user_id)
                if update_user:
                    u_data["admin_name"] = update_user.get_full_name()
                    u_data["admin_role"] = update_user.role
                updates_with_user.append(u_data)
            data["updates"] = updates_with_user

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@resident_bp.route("/properties", methods=["GET"])
@jwt_required()
def get_my_properties():
    try:
        resident = get_current_resident()
        if not resident:
            return jsonify({"error": "Resident not found"}), 404

        props = []
        for p in resident.properties:
            d = p.to_dict()
            if p.meters:
                d["meters"] = [m.to_dict() for m in p.meters]
            props.append(d)

        return jsonify(props), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
