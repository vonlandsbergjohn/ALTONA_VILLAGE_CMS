# altona_village_cms/src/routes/auth.py
from datetime import timedelta
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    verify_jwt_in_request,
)
from src.models.user import User, Resident, Owner, db
from src.utils.email_service import send_registration_notification_to_admin

# Prefer importing the real logger + normalizer; fallback to safe no-ops
try:
    from src.routes.admin_notifications import log_user_change, normalize_field_name
except Exception:
    def log_user_change(*args, **kwargs):
        pass
    def normalize_field_name(name: str) -> str:
        return name


def parse_address(address: str):
    """Parse a free-form address into street number + name, with some cleanup."""
    if not address:
        return "", ""

    address = (
        address.replace("Altona Village", "")
        .replace("Worcester", "")
        .strip()
    )

    parts = address.split()
    street_number = ""
    street_name = ""

    if parts:
        if parts[0].isdigit():
            street_number = parts[0]
            street_name = " ".join(parts[1:]).strip()
        elif parts[-1].isdigit():
            street_number = parts[-1]
            street_name = " ".join(parts[:-1]).strip()
        else:
            for i, part in enumerate(parts):
                if part.isdigit():
                    street_number = part
                    street_name = " ".join(parts[:i] + parts[i + 1:]).strip()
                    break
            if not street_number:
                street_name = address

    return street_number or "", street_name or address


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Registration always creates a PENDING account.
    Owner/Resident rows are created if the flags are set.
    """
    try:
        data = request.get_json() or {}

        # Required fields
        required = [
            "email",
            "password",
            "first_name",
            "last_name",
            "id_number",
            "erf_number",
            "is_owner",
            "is_resident",
        ]
        for field in required:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400

        # Require either (address) OR (street_number + street_name)
        if not (
            data.get("address")
            or (data.get("street_number") and data.get("street_name"))
        ):
            return jsonify(
                {
                    "error": "Address information is required (either address or street_number + street_name)"
                }
            ), 400

        # NOTE: allowing duplicate emails (multi-ERF); admin approval gate does the validation.

        # Create the user in PENDING
        user = User(
            email=data["email"],
            role="pending",   # your app promotes this once approved
            status="pending",
        )
        user.set_password(data["password"])
        db.session.add(user)
        db.session.flush()  # ensure user.id

        # Build address bits once when needed
        def _addr_from_payload():
            if "street_number" in data and "street_name" in data:
                sn = (data.get("street_number") or "").strip()
                sm = (data.get("street_name") or "").strip()
                return sn, sm, f"{sn} {sm}".strip()
            # fallback to parse combined address
            sn, sm = parse_address(data.get("address") or "")
            return sn, sm, (data.get("address") or "").strip()

        # Resident (if checked)
        if data.get("is_resident"):
            street_number, street_name, full_address = _addr_from_payload()
            resident = Resident(
                user_id=user.id,
                first_name=data["first_name"],
                last_name=data["last_name"],
                phone_number=data.get("phone_number"),
                emergency_contact_name=data.get("emergency_contact_name"),
                emergency_contact_number=data.get("emergency_contact_number"),
                id_number=data["id_number"],
                erf_number=data["erf_number"],
                street_number=street_number,
                street_name=street_name,
                full_address=full_address,
            )
            db.session.add(resident)

        # Owner (if checked)
        if data.get("is_owner"):
            street_number, street_name, full_address = _addr_from_payload()
            owner = Owner(
                user_id=user.id,
                first_name=data["first_name"],
                last_name=data["last_name"],
                phone_number=data.get("phone_number"),
                emergency_contact_name=data.get("emergency_contact_name"),
                emergency_contact_number=data.get("emergency_contact_number"),
                id_number=data["id_number"],
                erf_number=data["erf_number"],
                street_number=street_number,
                street_name=street_name,
                full_address=full_address,
                full_postal_address=data.get("postal_address"),
                title_deed_number=data.get("title_deed_number"),
            )
            db.session.add(owner)

        db.session.commit()

        # Best effort: notify admin
        try:
            send_registration_notification_to_admin(
                user.email, data["first_name"], data["last_name"]
            )
        except Exception as email_error:
            # log to console but don't fail registration
            print(f"Admin notification email failed: {email_error}")

        return jsonify(
            {
                "message": "Registration successful. Your application is pending admin approval. You will receive an email notification once approved.",
                "user_id": user.id,
                "status": "pending",
            }
        ), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/login", methods=["POST", "OPTIONS"])
@cross_origin(
    supports_credentials=True,
    origins=[
        "https://altona-village-frontend.onrender.com",
        "http://localhost:5173",  # helpful for local dev; safe to keep
    ],
    allow_headers=["Authorization", "Content-Type"],
)
def login():
    if request.method == "OPTIONS":
        return ("", 204)

    """
    Admin can ALWAYS log in, even if status isn't 'active' (we auto-activate them).
    All other roles must be 'active'.
    """
    try:
        data = request.get_json() or {}
        email = (data.get("email") or "").strip()
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({"error": "Invalid email or password"}), 401

        # Admin bypass + auto-activate safeguard
        if user.role == "admin":
            if user.status != "active":
                user.status = "active"
                db.session.commit()
        else:
            # Non-admin users must be active
            if user.status != "active":
                if user.status == "pending":
                    return jsonify(
                        {
                            "error": "Your account is still pending admin approval. You will receive an email notification once approved."
                        }
                    ), 401
                return jsonify(
                    {"error": "Account not activated. Please contact admin."}
                ), 401

        access_token = create_access_token(
            identity=user.id, expires_delta=timedelta(days=7)
        )
        return jsonify({"access_token": access_token, "user": user.to_dict()}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/profile", methods=["GET", "OPTIONS"])
@cross_origin(
    supports_credentials=True,
    origins=[
        "https://altona-village-frontend.onrender.com",
        "http://localhost:5173",
    ],
)
def profile():
    if request.method == "OPTIONS":
        return ("", 204)  # allow CORS preflight

    verify_jwt_in_request()          # replaces the old @jwt_required()
    user_id = get_jwt_identity()

    """
    Returns a consolidated profile for all accounts sharing the same email:
    a list of ERFs with role/status/type details plus legacy fields for the UI.
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    all_accounts = User.query.filter_by(email=user.email).all()

    erfs = []
    primary_profile = None

    for acct in all_accounts:
        # Default fallback
        base = {
            "user_id": acct.id,
            "status": acct.status,
            "role": acct.role,
            "is_current_account": acct.id == user.id,
            "type": "unknown",
            "erf_number": "Unknown",
            "full_name": "Unknown User",
            "full_address": "Address not available",
            "intercom_code": "Not available",
        }

        # Merge resident details (if any)
        if acct.resident:
            r = acct.resident
            base.update(
                {
                    "erf_number": r.erf_number or "Unknown",
                    "type": "resident",
                    "full_name": f"{(r.first_name or '').strip()} {(r.last_name or '').strip()}".strip()
                    or "Unknown User",
                    "street_number": r.street_number,
                    "street_name": r.street_name,
                    "full_address": r.full_address or "Address not available",
                    "phone_number": r.phone_number,
                    "emergency_contact_name": r.emergency_contact_name,
                    "emergency_contact_number": r.emergency_contact_number,
                    "intercom_code": r.intercom_code or "Not available",
                    "id_number": r.id_number,
                }
            )

        # Merge owner details (if any)
        if acct.owner:
            o = acct.owner
            # If we already tagged as resident above, this becomes owner-resident.
            if base["type"] == "resident":
                base["type"] = "owner-resident"
            else:
                base["type"] = "owner"

            base.update(
                {
                    "erf_number": o.erf_number or base.get("erf_number", "Unknown"),
                    "full_name": f"{(o.first_name or '').strip()} {(o.last_name or '').strip()}".strip()
                    or base.get("full_name", "Unknown User"),
                    "street_number": o.street_number or base.get("street_number"),
                    "street_name": o.street_name or base.get("street_name"),
                    "full_address": o.full_address or base.get("full_address"),
                    "phone_number": o.phone_number or base.get("phone_number"),
                    "id_number": o.id_number or base.get("id_number"),
                }
            )

        erfs.append(base)

        # choose first ACTIVE account as "primary profile" (temporary)
        if not primary_profile and acct.status == "active":
            primary_profile = base.copy()

    # --- PATCH: prefer Resident / Owner-Resident for banner fields ---
    if erfs:
        preferred = next((e for e in erfs if e.get("type") in ("resident", "owner-resident")), None)
        if preferred:
            primary_profile = preferred.copy()
        elif not primary_profile:
            primary_profile = erfs[0]
    # ----------------------------------------------------------------

    profile_data = {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "status": user.status,
        "total_erfs": len(erfs),
        "erfs": erfs,
        # Legacy top-level fields for UI compatibility
        "full_name": (primary_profile or {}).get("full_name", ""),
        "phone": (primary_profile or {}).get("phone_number", ""),
        "property_address": (primary_profile or {}).get("full_address", ""),
        "emergency_contact_name": (primary_profile or {}).get("emergency_contact_name", ""),
        "emergency_contact_phone": (primary_profile or {}).get("emergency_contact_number", ""),
        "intercom_code": (primary_profile or {}).get("intercom_code", ""),
        "erf_number": (primary_profile or {}).get("erf_number", ""),
        "tenant_or_owner": (primary_profile or {}).get("type", ""),
        "is_resident": any(erf.get("type") in ["resident", "owner-resident"] for erf in erfs),
        "is_owner": any(erf.get("type") in ["owner", "owner-resident"] for erf in erfs),
        "is_owner_resident": any(erf.get("type") == "owner-resident" for erf in erfs),
    }

    return jsonify(profile_data), 200


@auth_bp.route("/profile", methods=["PUT", "OPTIONS"])
@cross_origin(
    supports_credentials=True,
    origins=[
        "https://altona-village-frontend.onrender.com",
        "http://localhost:5173",
    ],
)
def update_profile():
    if request.method == "OPTIONS":
        return ("", 204)

    verify_jwt_in_request()
    current_user = User.query.get(get_jwt_identity())
    if not current_user:
        return jsonify({"error": "User not found"}), 404

    """
    Minimal, safe profile updater. Updates only known Resident/Owner fields if present.
    Logs changes via admin_notifications (if available).
    """
    try:
        data = request.get_json() or {}

        def _track(field_name, old_value, new_value, change_type="profile_update"):
            # Only record when the value truly changes
            if old_value == new_value:
                return

            # Normalize to the names Admin expects (e.g. phone_number -> cellphone_number)
            field_name = normalize_field_name(field_name)

            # Build a friendly name and ERF
            user_name = (
                f"{getattr(current_user.resident, 'first_name', '') or getattr(current_user.owner, 'first_name', '')} "
                f"{getattr(current_user.resident, 'last_name', '') or getattr(current_user.owner, 'last_name', '')}"
            ).strip() or (current_user.email or "Unknown")

            erf_number = (
                getattr(current_user.resident, "erf_number", "")
                or getattr(current_user.owner, "erf_number", "")
                or "Unknown"
            )

            try:
                log_user_change(
                    user_id=current_user.id,
                    user_name=user_name,
                    erf_number=erf_number,
                    change_type=change_type,
                    field_name=field_name,
                    old_value=str(old_value) if old_value is not None else "",
                    new_value=str(new_value) if new_value is not None else "",
                )
            except Exception as e:
                # Do not break the update flow due to logging
                print(f"Failed to log change for {field_name}: {e}")

        # Update Resident fields if exists
        if current_user.resident:
            r = current_user.resident
            for key in [
                "phone_number",
                "emergency_contact_name",
                "emergency_contact_number",
                "intercom_code",
                "full_address",
                "street_number",
                "street_name",
            ]:
                if key in data:
                    _track(key, getattr(r, key), data[key])
                    setattr(r, key, data[key])

        # Update Owner fields if exists
        if current_user.owner:
            o = current_user.owner
            for key in [
                "phone_number",
                "full_address",
                "street_number",
                "street_name",
                "full_postal_address",
                "title_deed_number",
            ]:
                if key in data:
                    _track(key, getattr(o, key), data[key])
                    setattr(o, key, data[key])

        db.session.commit()
        return jsonify({"message": "Profile updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
