from flask import Blueprint, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from collections import defaultdict
import csv
import io

from src.models.user import db, User, Resident, Owner, Vehicle

gate_register_bp = Blueprint("gate_register", __name__)

# Fields that should trigger a red/high-attention state in the Gate Register
CRITICAL_FIELDS = ("cellphone_number", "vehicle_registration", "vehicle_registration_2")


def _is_active_status(model_obj) -> bool:
    """
    Treat missing/None status as active to be permissive.
    Works for Resident/Owner models that may or may not have a 'status' column.
    """
    status = getattr(model_obj, "status", None)
    if status is None:
        return True
    return status in ("active", "approved")


def _admin_required() -> User | None:
    uid = get_jwt_identity()
    u = User.query.get(uid)
    return u if u and u.role == "admin" else None


def _build_gate_entries(active_users, pending_map, latest_map):
    """
    Convert a list of active users into gate entries.
    pending_map: dict(user_id -> set of critical fields pending review)
    latest_map:  dict(user_id -> latest change timestamp)
    """
    gate_entries = []

    for user in active_users:
        # skip admin accounts
        if user.role == "admin":
            continue

        resident_data = user.resident if user.is_resident() else None
        owner_data = user.owner if user.is_owner() else None

        # decide status label
        if resident_data and owner_data:
            status_label = "Owner-Resident"
        elif resident_data:
            status_label = "Resident"
        elif owner_data:
            status_label = "Owner"
        else:
            # no resident/owner data — skip from gate register
            continue

        # prefer resident as the "primary" record (intercom, address)
        primary = resident_data or owner_data

        # only include if their attached person records are "active/approved"
        if resident_data and not _is_active_status(resident_data):
            continue
        if owner_data and not _is_active_status(owner_data):
            continue

        # vehicles: resident first, else owner
        vehicle_regs = []
        if resident_data:
            vehicle_regs = [
                v.registration_number
                for v in Vehicle.query.filter_by(resident_id=resident_data.id).all()
                if v.registration_number
            ]
        elif owner_data:
            vehicle_regs = [
                v.registration_number
                for v in Vehicle.query.filter_by(owner_id=owner_data.id).all()
                if v.registration_number
            ]

        # pending critical changes for this user
        pending_fields = sorted(list(pending_map.get(user.id, set())))
        has_critical = bool(pending_fields)

        entry = {
            "user_id": user.id,
            "resident_status": status_label,
            "surname": primary.last_name or "",
            "first_name": primary.first_name or "",
            "street_number": primary.street_number or "",
            "street_name": primary.street_name or "",
            "vehicle_registrations": vehicle_regs,  # list for JSON view
            "erf_number": primary.erf_number or "",
            "intercom_code": getattr(primary, "intercom_code", "") or "",
            "sort_key": (primary.street_name or "").upper(),
            # NEW flags for UI highlighting:
            "pending_critical_changes": has_critical,
            "pending_fields": pending_fields,
            "changes_count": len(pending_fields),
            "latest_change_at": latest_map.get(user.id),
        }

        gate_entries.append(entry)

    # sort alphabetically by street name
    gate_entries.sort(key=lambda x: x["sort_key"])
    return gate_entries


def _collect_pending_changes(user_ids):
    """
    Fetch unreviewed changes in one query and return:
      - pending_map: user_id -> set(field_names)
      - latest_map:  user_id -> ISO timestamp of latest critical change
    """
    pending_map: dict[str, set[str]] = defaultdict(set)
    latest_map: dict[str, str | None] = {}

    if not user_ids:
        return pending_map, latest_map

    # Lazy import to avoid import-time issues during migrations
    from src.models.user_change import UserChange

    rows = (
        UserChange.query.filter(
            UserChange.user_id.in_(user_ids),
            UserChange.admin_reviewed.is_(False),
            UserChange.field_name.in_(CRITICAL_FIELDS),
        )
        .all()
    )

    for r in rows:
        try:
            pending_map[r.user_id].add(r.field_name)
            ts = r.change_timestamp.isoformat() if r.change_timestamp else None
            if ts:
                prev = latest_map.get(r.user_id)
                if not prev or ts > prev:
                    latest_map[r.user_id] = ts
        except Exception:
            # don't break the page if an old row is malformed
            continue

    return pending_map, latest_map


# ------------------------------ JSON Register ------------------------------

@gate_register_bp.route("/gate-register", methods=["GET"])
@gate_register_bp.route("/gate-register-legacy", methods=["GET"])
@jwt_required()
def get_gate_register():
    """
    Generate gate register for security guards (JSON).
    Format (per row): RESIDENT STATUS, SURNAME, STREET NR, STREET NAME,
                      VEHICLE REGISTRATIONS (list), ERF NR, INTERCOM NR
    + NEW flags: pending_critical_changes, pending_fields, changes_count
    """
    admin = _admin_required()
    if not admin:
        return jsonify({"error": "Unauthorized access"}), 403

    try:
        # fetch active/approved user shell rows
        active_users = User.query.filter(User.status.in_(["active", "approved"])).all()
        user_ids = [u.id for u in active_users]

        # get all unreviewed critical changes (single query)
        pending_map, latest_map = _collect_pending_changes(user_ids)

        entries = _build_gate_entries(active_users, pending_map, latest_map)

        return jsonify(
            {
                "success": True,
                "data": entries,
                "total_entries": len(entries),
                "generated_at": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        return jsonify({"error": f"Failed to generate gate register: {e}"}), 500


# ------------------------------ CSV Export ------------------------------

@gate_register_bp.route("/gate-register/export", methods=["GET"])
@jwt_required()
def export_gate_register_csv():
    """
    Export gate register as CSV file for printing.
    NOTE: CSV columns remain unchanged to avoid breaking existing processes.
    """
    admin = _admin_required()
    if not admin:
        return jsonify({"error": "Unauthorized access"}), 403

    try:
        active_users = User.query.filter(User.status.in_(["active", "approved"])).all()
        user_ids = [u.id for u in active_users]

        # still compute pending to keep the same order as JSON
        pending_map, latest_map = _collect_pending_changes(user_ids)
        entries = _build_gate_entries(active_users, pending_map, latest_map)

        # Flatten to one row per vehicle (or blank if none), keep your original headers
        flat_rows = []
        for e in entries:
            regs = e["vehicle_registrations"] or [""]
            for reg in regs:
                flat_rows.append(
                    {
                        "resident_status": e["resident_status"],
                        "surname": e["surname"],
                        "street_number": e["street_number"],
                        "street_name": e["street_name"],
                        "vehicle_registration": reg,
                        "erf_number": e["erf_number"],
                        "intercom_code": e["intercom_code"],
                        "sort_key": e["sort_key"],
                    }
                )

        flat_rows.sort(key=lambda x: x["sort_key"])

        output = io.StringIO()
        writer = csv.writer(output)

        # header (unchanged)
        writer.writerow(
            [
                "RESIDENT STATUS",
                "SURNAME",
                "STREET NR",
                "STREET NAME",
                "VEHICLE REGISTRATION NR",
                "ERF NR",
                "INTERCOM NR",
            ]
        )

        for r in flat_rows:
            writer.writerow(
                [
                    r["resident_status"],
                    r["surname"],
                    r["street_number"],
                    r["street_name"],
                    r["vehicle_registration"],
                    r["erf_number"],
                    r["intercom_code"],
                ]
            )

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"gate_register_{timestamp}.csv"

        output.seek(0)
        csv_content = output.getvalue()
        output.close()

        return Response(
            csv_content,
            mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "text/csv; charset=utf-8",
            },
        )

    except Exception as e:
        return jsonify({"error": f"Failed to export gate register: {e}"}), 500
