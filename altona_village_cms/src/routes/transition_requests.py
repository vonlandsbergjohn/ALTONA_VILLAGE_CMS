from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date
from werkzeug.security import generate_password_hash

# Models (absolute import to avoid the previous "unknown location" error)
from src.models.user import (
    db, User, Resident, Owner, UserTransitionRequest,
    TransitionRequestUpdate, TransitionVehicle, Vehicle
)

# Same-package import for notifications (no relative ".." needed)
from .admin_notifications import log_user_change

# Define ONE blueprint; main.py registers this at /api/transition
transition_bp = Blueprint("transition", __name__)


# --- ADMIN: Link two existing transition requests (owner <-> tenant) for same ERF ---
@transition_bp.route('/admin/link-existing-requests', methods=['POST'])
@jwt_required()
def link_existing_transition_requests():
    """Link two existing transition requests for the same ERF (owner and tenant), process migration, and update statuses."""
    current_user = User.query.get(get_jwt_identity())
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json() or {}
    owner_request_id = data.get('owner_request_id')
    tenant_request_id = data.get('tenant_request_id')

    if not owner_request_id or not tenant_request_id:
        return jsonify({'error': 'Both request IDs are required'}), 400

    owner_request = UserTransitionRequest.query.get(owner_request_id)
    tenant_request = UserTransitionRequest.query.get(tenant_request_id)

    if not owner_request or not tenant_request:
        return jsonify({'error': 'One or both transition requests not found'}), 404

    # Must be for the same ERF and not completed
    if owner_request.erf_number != tenant_request.erf_number:
        return jsonify({'error': 'Transition requests are for different ERFs'}), 400
    if owner_request.status == 'completed' or tenant_request.status == 'completed':
        return jsonify({'error': 'One or both transition requests are already completed'}), 400

    # Check roles based on records
    owner_user = User.query.get(owner_request.user_id)
    tenant_user = User.query.get(tenant_request.user_id)
    if not owner_user or not tenant_user:
        return jsonify({'error': 'One or both users not found'}), 404

    owner_is_owner = Owner.query.filter_by(user_id=owner_user.id, erf_number=owner_request.erf_number).first() is not None
    tenant_is_resident = Resident.query.filter_by(user_id=tenant_user.id, erf_number=tenant_request.erf_number).first() is not None
    if not owner_is_owner or not tenant_is_resident:
        return jsonify({'error': 'Role mismatch: expected owner and resident records for ERF'}), 400

    # Process: make tenant the new owner-resident, deactivate seller
    try:
        # Deactivate seller (owner)
        owner_user.status = 'inactive'
        owner_request.status = 'completed'
        owner_request.completed_at = datetime.utcnow()

        # Update tenant to owner-resident
        tenant_user.role = 'owner_resident'
        tenant_request.status = 'completed'
        tenant_request.completed_at = datetime.utcnow()

        # Remove old owner record
        Owner.query.filter_by(user_id=owner_user.id, erf_number=owner_request.erf_number).delete()

        # Add new owner record for tenant
        new_owner = Owner(
            user_id=tenant_user.id,
            erf_number=tenant_request.erf_number,
            first_name=getattr(tenant_user, "first_name", ""),
            last_name=getattr(tenant_user, "last_name", ""),
            phone_number=getattr(tenant_user, "phone_number", "")
        )
        db.session.add(new_owner)

        # Optionally update Resident record for tenant (set is_owner=True if field exists)
        resident_record = Resident.query.filter_by(user_id=tenant_user.id, erf_number=tenant_request.erf_number).first()
        if resident_record and hasattr(resident_record, "is_owner"):
            resident_record.is_owner = True

        db.session.commit()
        return jsonify({'success': True, 'message': 'Transition requests linked and migration processed.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to process migration: {str(e)}'}), 500


# ------------- Core migration helpers (3 scenarios) ----------------

def perform_user_migration(transition_request):
    """
    Comprehensive migration for legacy requests that included new-occupant data.
    Scenarios:
      1) Complete replacement (different people)
      2) Role change (same person)
      3) Partial replacement (existing other user gets new role)
    """
    try:
        # Validate required data
        if (not transition_request.new_occupant_type or
            transition_request.new_occupant_type == 'unknown' or
            not transition_request.new_occupant_first_name or
            not transition_request.new_occupant_last_name):
            return {'success': True, 'message': 'No new occupant data to migrate'}

        current_user = User.query.get(transition_request.user_id)
        if not current_user:
            return {'success': False, 'error': 'Current user not found'}

        new_occupant_email = transition_request.new_occupant_email or (
            f"temp_{transition_request.new_occupant_first_name.lower()}_"
            f"{transition_request.new_occupant_last_name.lower()}@altona-village.temp"
        )

        is_same_person = (current_user.email == new_occupant_email)
        existing_new_user = (
            None if is_same_person
            else User.query.filter_by(email=new_occupant_email).first()
        )

        if is_same_person:
            return handle_role_change_migration(transition_request, current_user)
        elif existing_new_user:
            return handle_partial_replacement_migration(transition_request, current_user, existing_new_user)
        else:
            return handle_complete_user_replacement(transition_request, current_user, new_occupant_email)

    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': f'Migration failed: {str(e)}'}


def handle_role_change_migration(transition_request, current_user):
    """Same person changes roles, keep account & password."""
    try:
        erf_number = transition_request.erf_number
        new_type = transition_request.new_occupant_type  # resident | owner | owner_resident

        # Update user.role
        if new_type in ('resident', 'owner', 'owner_resident'):
            current_user.role = new_type

        # Resident record
        existing_resident = current_user.resident
        if new_type in ('resident', 'owner_resident'):
            if not existing_resident:
                new_resident = Resident(
                    user_id=current_user.id,
                    first_name=transition_request.new_occupant_first_name,
                    last_name=transition_request.new_occupant_last_name,
                    erf_number=erf_number,
                    phone_number=transition_request.new_occupant_phone or '',
                    id_number=transition_request.new_occupant_id_number or '999999999',
                    street_number=transition_request.new_occupant_street_number or '1',
                    street_name=transition_request.new_occupant_street_name or 'Main Street',
                    full_address=transition_request.new_occupant_full_address or f'{erf_number} Main Street',
                    intercom_code=transition_request.new_occupant_intercom_code or 'ADMIN_SET_REQUIRED',
                    status='active'
                )
                db.session.add(new_resident)
            else:
                existing_resident.status = 'active'
                existing_resident.erf_number = erf_number
        else:
            if existing_resident:
                existing_resident.status = 'inactive'

        # Owner record
        existing_owner = current_user.owner
        if new_type in ('owner', 'owner_resident'):
            if not existing_owner:
                new_owner = Owner(
                    user_id=current_user.id,
                    first_name=transition_request.new_occupant_first_name,
                    last_name=transition_request.new_occupant_last_name,
                    erf_number=erf_number,
                    phone_number=transition_request.new_occupant_phone or '',
                    id_number=transition_request.new_occupant_id_number or '999999999',
                    street_number=transition_request.new_occupant_street_number or '1',
                    street_name=transition_request.new_occupant_street_name or 'Main Street',
                    full_address=transition_request.new_occupant_full_address or f'{erf_number} Main Street',
                    intercom_code=transition_request.new_occupant_intercom_code or 'ADMIN_SET_REQUIRED',
                    title_deed_number=transition_request.new_occupant_title_deed_number or 'T000000',
                    postal_street_number=transition_request.new_occupant_postal_street_number or '1',
                    postal_street_name=transition_request.new_occupant_postal_street_name or 'Main Street',
                    postal_suburb=transition_request.new_occupant_postal_suburb or 'Suburb',
                    postal_city=transition_request.new_occupant_postal_city or 'City',
                    postal_code=transition_request.new_occupant_postal_code or '0000',
                    postal_province=transition_request.new_occupant_postal_province or 'Province',
                    full_postal_address=transition_request.new_occupant_full_postal_address or '1 Main Street, Suburb, City, 0000',
                    status='active'
                )
                db.session.add(new_owner)
            else:
                existing_owner.status = 'active'
                existing_owner.erf_number = erf_number
        else:
            if existing_owner:
                existing_owner.status = 'inactive'

        # Mark migration
        transition_request.migration_completed = True
        transition_request.migration_date = datetime.utcnow()
        transition_request.new_user_id = current_user.id

        db.session.commit()
        return {
            'success': True,
            'message': f'Role change completed: {current_user.email} → {current_user.role} for ERF {erf_number}',
            'migration_type': 'role_change',
            'user_id': current_user.id,
            'password_preserved': True
        }
    except Exception as e:
        db.session.rollback()
        raise e


def handle_partial_replacement_migration(transition_request, old_user, new_user):
    """
    Existing (different) user gets an additional role; old user is deactivated.
    Example: owner moves in, tenant moves out.
    """
    try:
        erf_number = transition_request.erf_number
        new_type = transition_request.new_occupant_type  # resident | owner | owner_resident

        # Deactivate old user
        old_user.status = 'inactive'
        old_user.password_hash = 'DISABLED'

        # Mark old records deleted_profile
        migration_reason = f'Replaced by existing user {new_user.email} via transition {transition_request.id}'
        now = datetime.utcnow()
        if old_user.resident:
            old_user.resident.status = 'deleted_profile'
            old_user.resident.migration_date = now
            old_user.resident.migration_reason = migration_reason
        if old_user.owner:
            old_user.owner.status = 'deleted_profile'
            old_user.owner.migration_date = now
            old_user.owner.migration_reason = migration_reason

        # Add roles to new user as needed
        if new_type in ('resident', 'owner_resident') and not new_user.resident:
            new_resident = Resident(
                user_id=new_user.id,
                first_name=transition_request.new_occupant_first_name,
                last_name=transition_request.new_occupant_last_name,
                erf_number=erf_number,
                phone_number=transition_request.new_occupant_phone or '',
                id_number=transition_request.new_occupant_id_number or '999999999',
                street_number=transition_request.new_occupant_street_number or '1',
                street_name=transition_request.new_occupant_street_name or 'Main Street',
                full_address=transition_request.new_occupant_full_address or f'{erf_number} Main Street',
                intercom_code=transition_request.new_occupant_intercom_code or 'ADMIN_SET_REQUIRED',
                status='active'
            )
            db.session.add(new_resident)

        if new_type in ('owner', 'owner_resident') and not new_user.owner:
            new_owner = Owner(
                user_id=new_user.id,
                first_name=transition_request.new_occupant_first_name,
                last_name=transition_request.new_occupant_last_name,
                erf_number=erf_number,
                phone_number=transition_request.new_occupant_phone or '',
                id_number=transition_request.new_occupant_id_number or '999999999',
                street_number=transition_request.new_occupant_street_number or '1',
                street_name=transition_request.new_occupant_street_name or 'Main Street',
                full_address=transition_request.new_occupant_full_address or f'{erf_number} Main Street',
                intercom_code=transition_request.new_occupant_intercom_code or 'ADMIN_SET_REQUIRED',
                title_deed_number=transition_request.new_occupant_title_deed_number or 'T000000',
                postal_street_number=transition_request.new_occupant_postal_street_number or '1',
                postal_street_name=transition_request.new_occupant_postal_street_name or 'Main Street',
                postal_suburb=transition_request.new_occupant_postal_suburb or 'Suburb',
                postal_city=transition_request.new_occupant_postal_city or 'City',
                postal_code=transition_request.new_occupant_postal_code or '0000',
                postal_province=transition_request.new_occupant_postal_province or 'Province',
                full_postal_address=transition_request.new_occupant_full_postal_address or '1 Main Street, Suburb, City, 0000',
                status='active'
            )
            db.session.add(new_owner)

        # Update new user's top-level role (avoid downgrading owner_resident)
        if new_type == 'owner_resident':
            new_user.role = 'owner_resident'
        elif new_type == 'owner' and new_user.role != 'owner_resident':
            new_user.role = 'owner'
        elif new_type == 'resident' and new_user.role != 'owner_resident':
            new_user.role = 'resident'

        transition_request.migration_completed = True
        transition_request.migration_date = datetime.utcnow()
        transition_request.new_user_id = new_user.id

        db.session.commit()
        return {
            'success': True,
            'message': f'Partial replacement: {old_user.email} → {new_user.email} for ERF {erf_number}',
            'migration_type': 'partial_replacement',
            'old_user_id': old_user.id,
            'new_user_id': new_user.id
        }
    except Exception as e:
        db.session.rollback()
        raise e


def handle_complete_user_replacement(transition_request, old_user, new_email):
    """Different person entirely: deactivate old, create brand new user + role records."""
    try:
        erf_number = transition_request.erf_number
        migration_reason = f'Replaced by new user {new_email} via transition {transition_request.id}'
        now = datetime.utcnow()

        # Deactivate old user and mark records
        old_user.status = 'inactive'
        old_user.password_hash = 'DISABLED'
        if old_user.resident:
            old_user.resident.status = 'deleted_profile'
            old_user.resident.migration_date = now
            old_user.resident.migration_reason = migration_reason
        if old_user.owner:
            old_user.owner.status = 'deleted_profile'
            old_user.owner.migration_date = now
            old_user.owner.migration_reason = migration_reason

        # Deactivate vehicles on old user
        old_vehicles = []
        if old_user.resident:
            old_vehicles.extend(Vehicle.query.filter_by(resident_id=old_user.resident.id).all())
        if old_user.owner:
            old_vehicles.extend(Vehicle.query.filter_by(owner_id=old_user.owner.id).all())
        for v in old_vehicles:
            v.status = 'inactive'
            v.migration_date = now
            v.migration_reason = migration_reason

        # Create the new user
        temp_password = 'test'
        new_user = User(
            email=new_email,
            password_hash=generate_password_hash(temp_password),
            role='resident',
            status='active'
        )
        db.session.add(new_user)
        db.session.flush()  # get new_user.id

        # Role records for new user
        new_type = transition_request.new_occupant_type  # resident|owner|owner_resident
        if new_type == 'resident':
            db.session.add(Resident(
                user_id=new_user.id,
                first_name=transition_request.new_occupant_first_name,
                last_name=transition_request.new_occupant_last_name,
                erf_number=erf_number,
                phone_number=transition_request.new_occupant_phone or '',
                id_number=transition_request.new_occupant_id_number or '999999999',
                street_number=transition_request.new_occupant_street_number or '1',
                street_name=transition_request.new_occupant_street_name or 'Main Street',
                full_address=transition_request.new_occupant_full_address or f'{erf_number} Main Street',
                intercom_code=transition_request.new_occupant_intercom_code or 'ADMIN_SET_REQUIRED',
                status='active'
            ))
            new_user.role = 'resident'

        elif new_type == 'owner':
            db.session.add(Owner(
                user_id=new_user.id,
                first_name=transition_request.new_occupant_first_name,
                last_name=transition_request.new_occupant_last_name,
                erf_number=erf_number,
                phone_number=transition_request.new_occupant_phone or '',
                id_number=transition_request.new_occupant_id_number or '999999999',
                street_number=transition_request.new_occupant_street_number or '1',
                street_name=transition_request.new_occupant_street_name or 'Main Street',
                full_address=transition_request.new_occupant_full_address or f'{erf_number} Main Street',
                intercom_code=transition_request.new_occupant_intercom_code or 'ADMIN_SET_REQUIRED',
                title_deed_number=transition_request.new_occupant_title_deed_number or 'T000000',
                postal_street_number=transition_request.new_occupant_postal_street_number or '1',
                postal_street_name=transition_request.new_occupant_postal_street_name or 'Main Street',
                postal_suburb=transition_request.new_occupant_postal_suburb or 'Suburb',
                postal_city=transition_request.new_occupant_postal_city or 'City',
                postal_code=transition_request.new_occupant_postal_code or '0000',
                postal_province=transition_request.new_occupant_postal_province or 'Province',
                full_postal_address='1 Main Street, Suburb, City, 0000',
                status='active'
            ))
            new_user.role = 'owner'

        elif new_type == 'owner_resident':
            db.session.add(Resident(
                user_id=new_user.id,
                first_name=transition_request.new_occupant_first_name,
                last_name=transition_request.new_occupant_last_name,
                erf_number=erf_number,
                phone_number=transition_request.new_occupant_phone or '',
                id_number=transition_request.new_occupant_id_number or '999999999',
                street_number=transition_request.new_occupant_street_number or '1',
                street_name=transition_request.new_occupant_street_name or 'Main Street',
                full_address=transition_request.new_occupant_full_address or f'{erf_number} Main Street',
                intercom_code=transition_request.new_occupant_intercom_code or 'ADMIN_SET_REQUIRED',
                status='active'
            ))
            db.session.add(Owner(
                user_id=new_user.id,
                first_name=transition_request.new_occupant_first_name,
                last_name=transition_request.new_occupant_last_name,
                erf_number=erf_number,
                phone_number=transition_request.new_occupant_phone or '',
                id_number=transition_request.new_occupant_id_number or '999999999',
                street_number=transition_request.new_occupant_street_number or '1',
                street_name=transition_request.new_occupant_street_name or 'Main Street',
                full_address=transition_request.new_occupant_full_address or f'{erf_number} Main Street',
                intercom_code=transition_request.new_occupant_intercom_code or 'ADMIN_SET_REQUIRED',
                title_deed_number=transition_request.new_occupant_title_deed_number or 'T000000',
                postal_street_number='1',
                postal_street_name='Main Street',
                postal_suburb='Suburb',
                postal_city='City',
                postal_code='0000',
                postal_province='Province',
                full_postal_address='1 Main Street, Suburb, City, 0000',
                status='active'
            ))
            new_user.role = 'owner_resident'

        # Mark migration
        transition_request.migration_completed = True
        transition_request.migration_date = now
        transition_request.new_user_id = new_user.id

        db.session.commit()
        return {
            'success': True,
            'message': f'Complete replacement: {old_user.email} → {new_email} (temp password set)',
            'migration_type': 'complete_replacement',
            'old_user_id': old_user.id,
            'new_user_id': new_user.id,
            'new_password': temp_password
        }
    except Exception as e:
        db.session.rollback()
        raise e


# ----------------------- Public user endpoints -----------------------

@transition_bp.route('/request', methods=['POST'])
@jwt_required()
def create_transition_request():
    """Create a new user transition request"""
    try:
        current_user_id = get_jwt_identity()
        data = (request.get_json() or {})

        # Validate required fields
        required = ['erf_number', 'request_type', 'current_role', 'new_occupant_type']
        for field in required:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Validate enums
        valid_request_types = ['owner_sale', 'tenant_moveout', 'owner_moving', 'other']
        if data['request_type'] not in valid_request_types:
            return jsonify({'error': 'Invalid request type'}), 400

        valid_occupant_types = ['resident', 'owner', 'owner_resident', 'terminated']
        if data['new_occupant_type'] not in valid_occupant_types:
            return jsonify({'error': 'Invalid future residency status'}), 400

        valid_roles = ['owner', 'tenant', 'owner_resident']
        if data['current_role'] not in valid_roles:
            return jsonify({'error': 'Invalid current role'}), 400

        # Create
        transition_request = UserTransitionRequest(
            user_id=current_user_id,
            erf_number=data['erf_number'],
            request_type=data['request_type'],
            current_role=data['current_role'],
            new_occupant_type=data['new_occupant_type']
        )

        # Dates
        date_fields = [
            'intended_moveout_date', 'property_transfer_date', 'new_occupant_movein_date',
            'expected_transfer_date', 'lease_end_date', 'rental_start_date'
        ]
        for f in date_fields:
            if data.get(f):
                try:
                    setattr(transition_request, f, datetime.strptime(data[f], '%Y-%m-%d').date())
                except ValueError:
                    return jsonify({'error': f'Invalid date format for {f}. Use YYYY-MM-DD'}), 400

        # Text fields
        text_fields = [
            'notice_period', 'transfer_attorney', 'moveout_reason', 'moveout_reason_other',
            'property_management_company', 'outstanding_matters_other',
            'new_occupant_name', 'new_occupant_phone', 'new_occupant_email',
            'access_handover_requirements', 'property_condition_notes', 'community_introduction_needs'
        ]
        for f in text_fields:
            if f in data:
                setattr(transition_request, f, data.get(f))

        # Booleans
        boolean_fields = [
            'sale_agreement_signed', 'new_owner_details_known', 'deposit_return_required',
            'new_tenant_selected', 'gate_access_transfer', 'intercom_access_transfer',
            'vehicle_registration_transfer', 'visitor_access_transfer', 'community_notifications_transfer',
            'unpaid_levies', 'pending_maintenance', 'community_violations'
        ]
        for f in boolean_fields:
            if f in data:
                setattr(transition_request, f, bool(data.get(f)))

        # Integers
        for f in ['new_occupant_adults', 'new_occupant_children', 'new_occupant_pets']:
            if data.get(f) not in (None, ''):
                try:
                    setattr(transition_request, f, int(data.get(f)))
                except (ValueError, TypeError):
                    setattr(transition_request, f, 0)

        # Priority by notice period
        if data.get('intended_moveout_date'):
            moveout_date = datetime.strptime(data['intended_moveout_date'], '%Y-%m-%d').date()
            days_notice = (moveout_date - date.today()).days
            if days_notice < 7:
                transition_request.priority = 'emergency'
            elif days_notice < 30:
                transition_request.priority = 'urgent'
            else:
                transition_request.priority = 'standard'

        db.session.add(transition_request)
        db.session.flush()

        # Vehicles
        if isinstance(data.get('vehicles'), list):
            for v in data['vehicles']:
                if v.get('license_plate'):
                    db.session.add(TransitionVehicle(
                        transition_request_id=transition_request.id,
                        vehicle_make=v.get('vehicle_make'),
                        vehicle_model=v.get('vehicle_model'),
                        license_plate=v.get('license_plate'),
                        color=v.get('color')
                    ))

        # Initial update
        db.session.add(TransitionRequestUpdate(
            transition_request_id=transition_request.id,
            user_id=current_user_id,
            update_text=f"Transition request submitted for ERF {data['erf_number']} - {data['request_type'].replace('_', ' ').title()}",
            update_type='comment'
        ))

        db.session.commit()
        return jsonify({
            'message': 'Transition request created successfully',
            'request_id': transition_request.id,
            'status': transition_request.status,
            'priority': transition_request.priority
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating transition request: {str(e)}")
        return jsonify({'error': 'Failed to create transition request'}), 500


@transition_bp.route('/requests', methods=['GET'])
@jwt_required()
def get_user_transition_requests():
    """Get transition requests for the current user"""
    try:
        current_user_id = get_jwt_identity()
        requests = UserTransitionRequest.query.filter_by(user_id=current_user_id) \
            .order_by(UserTransitionRequest.created_at.desc()).all()
        return jsonify({'requests': [r.to_dict() for r in requests]}), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching user transition requests: {str(e)}")
        return jsonify({'error': 'Failed to fetch requests'}), 500


@transition_bp.route('/request/<request_id>', methods=['GET'])
@jwt_required()
def get_transition_request(request_id):
    """Get details of a specific transition request"""
    try:
        current_user = User.query.get(get_jwt_identity())
        transition_request = UserTransitionRequest.query.get_or_404(request_id)

        if transition_request.user_id != current_user.id and current_user.role != 'admin':
            return jsonify({'error': 'Access denied'}), 403

        request_data = transition_request.to_dict()

        updates = TransitionRequestUpdate.query.filter_by(
            transition_request_id=request_id
        ).order_by(TransitionRequestUpdate.created_at.desc()).all()
        request_data['updates'] = [u.to_dict() for u in updates]

        vehicles = TransitionVehicle.query.filter_by(transition_request_id=request_id).all()
        request_data['vehicles'] = [v.to_dict() for v in vehicles]

        return jsonify(request_data), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching transition request: {str(e)}")
        return jsonify({'error': 'Failed to fetch request'}), 500


@transition_bp.route('/request/<request_id>/update', methods=['POST'])
@jwt_required()
def add_transition_request_update(request_id):
    """Add an update to a transition request"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json() or {}

        if not data.get('update_text'):
            return jsonify({'error': 'Update text is required'}), 400

        transition_request = UserTransitionRequest.query.get_or_404(request_id)

        current_user = User.query.get(current_user_id)
        if transition_request.user_id != current_user_id and current_user.role != 'admin':
            return jsonify({'error': 'Access denied'}), 403

        update = TransitionRequestUpdate(
            transition_request_id=request_id,
            user_id=current_user_id,
            update_text=data['update_text'],
            update_type=data.get('update_type', 'comment')
        )
        db.session.add(update)

        transition_request.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({'message': 'Update added successfully', 'update': update.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding transition request update: {str(e)}")
        return jsonify({'error': 'Failed to add update'}), 500


# ----------------------- Admin endpoints -----------------------

@transition_bp.route('/admin/requests', methods=['GET'])
@jwt_required()
def get_all_transition_requests():
    """Get all transition requests (admin only)"""
    try:
        current_user = User.query.get(get_jwt_identity())
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403

        status_filter = request.args.get('status')
        priority_filter = request.args.get('priority')
        erf_filter = request.args.get('erf_number')

        q = UserTransitionRequest.query
        if status_filter:
            q = q.filter(UserTransitionRequest.status == status_filter)
        if priority_filter:
            q = q.filter(UserTransitionRequest.priority == priority_filter)
        if erf_filter:
            q = q.filter(UserTransitionRequest.erf_number.contains(erf_filter))

        results = q.order_by(
            UserTransitionRequest.priority.desc(),
            UserTransitionRequest.created_at.desc()
        ).all()

        return jsonify({'requests': [r.to_dict() for r in results], 'total': len(results)}), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching admin transition requests: {str(e)}")
        return jsonify({'error': 'Failed to fetch requests'}), 500


@transition_bp.route('/admin/request/<request_id>', methods=['GET'])
@jwt_required()
def get_admin_transition_request_details(request_id):
    """Get detailed transition request information for admin"""
    try:
        current_user = User.query.get(get_jwt_identity())
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403

        request_obj = UserTransitionRequest.query.filter_by(id=request_id).first()
        if not request_obj:
            return jsonify({'error': 'Request not found'}), 404

        updates = TransitionRequestUpdate.query.filter_by(
            transition_request_id=request_id
        ).order_by(TransitionRequestUpdate.created_at.desc()).all()

        vehicles = TransitionVehicle.query.filter_by(
            transition_request_id=request_id
        ).all()

        payload = request_obj.to_dict()
        payload['updates'] = [u.to_dict() for u in updates]
        payload['vehicles'] = [v.to_dict() for v in vehicles]

        return jsonify(payload), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching admin transition request details: {str(e)}")
        return jsonify({'error': 'Failed to fetch request details'}), 500


@transition_bp.route('/admin/request/<request_id>/assign', methods=['PUT'])
@jwt_required()
def assign_transition_request(request_id):
    """Assign transition request to admin"""
    try:
        current_user = User.query.get(get_jwt_identity())
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403

        transition_request = UserTransitionRequest.query.get_or_404(request_id)
        data = request.get_json() or {}

        admin_id = data.get('admin_id', current_user.id)

        admin_user = User.query.get(admin_id)
        if not admin_user or admin_user.role != 'admin':
            return jsonify({'error': 'Invalid admin ID'}), 400

        old_admin = transition_request.assigned_admin
        transition_request.assigned_admin = admin_id
        transition_request.updated_at = datetime.utcnow()

        update_text = f"Request assigned to {admin_user.get_full_name()}"
        if old_admin:
            old_admin_user = User.query.get(old_admin)
            update_text = f"Request reassigned from {old_admin_user.get_full_name() if old_admin_user else 'Unknown'} to {admin_user.get_full_name()}"

        db.session.add(TransitionRequestUpdate(
            transition_request_id=request_id,
            user_id=current_user.id,
            update_text=update_text,
            update_type='admin_note'
        ))
        db.session.commit()

        return jsonify({'message': 'Request assigned successfully', 'assigned_to': admin_user.get_full_name()}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error assigning transition request: {str(e)}")
        return jsonify({'error': 'Failed to assign request'}), 500


@transition_bp.route('/admin/request/<request_id>/status', methods=['PUT'])
@jwt_required()
def update_transition_request_status(request_id):
    """Update transition request status (admin only)"""
    try:
        current_user = User.query.get(get_jwt_identity())
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403

        transition_request = UserTransitionRequest.query.get_or_404(request_id)
        data = request.get_json() or {}

        new_status = data.get('status')
        admin_notes = data.get('admin_notes')

        valid_statuses = [
            'pending_review', 'in_progress', 'awaiting_docs',
            'ready_for_transition', 'completed', 'cancelled'
        ]
        if new_status not in valid_statuses:
            return jsonify({'error': 'Invalid status'}), 400

        old_status = transition_request.status
        transition_request.status = new_status
        transition_request.updated_at = datetime.utcnow()
        if admin_notes:
            transition_request.admin_notes = admin_notes

        if new_status == 'completed':
            transition_request.completion_date = datetime.utcnow()

            is_termination = (
                transition_request.new_occupant_type == 'terminated' or
                transition_request.request_type == 'exit' or
                (transition_request.new_occupant_type in ['', 'unknown', None] and
                 not transition_request.new_occupant_first_name)
            )

            is_privacy_compliant = (
                not transition_request.new_occupant_first_name or
                not transition_request.new_occupant_last_name or
                not transition_request.new_occupant_type or
                transition_request.new_occupant_type in ['', 'unknown', None]
            )

            if is_termination:
                if not transition_request.migration_completed:
                    pending_user = find_pending_user_for_erf(transition_request.erf_number)
                    if pending_user:
                        return jsonify({
                            'error': f'Found pending user for ERF {transition_request.erf_number}. Use the Transition Linking interface.'
                        }), 400
                    else:
                        termination_result = handle_user_termination(transition_request)
                        if not termination_result['success']:
                            current_app.logger.error(f"User termination failed: {termination_result['error']}")
                            return jsonify({'error': f"Termination failed: {termination_result['error']}"}), 500
                        transition_request.migration_completed = True

            elif is_privacy_compliant:
                if not transition_request.migration_completed:
                    return jsonify({
                        'error': 'Privacy-compliant requests must be completed via the Transition Linking interface.'
                    }), 400
            else:
                migration_result = perform_user_migration(transition_request)
                if not migration_result['success']:
                    current_app.logger.error(f"User migration failed: {migration_result['error']}")
                    return jsonify({'error': f"Migration failed: {migration_result['error']}"}), 500

        db.session.add(TransitionRequestUpdate(
            transition_request_id=request_id,
            user_id=current_user.id,
            update_text=data.get('update_message', f"Status changed from {old_status} to {new_status}"),
            update_type='status_change',
            old_status=old_status,
            new_status=new_status
        ))
        db.session.commit()

        return jsonify({'message': 'Status updated successfully', 'old_status': old_status, 'new_status': new_status}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating transition request status: {str(e)}")
        return jsonify({'error': 'Failed to update status'}), 500


@transition_bp.route('/admin/request/<request_id>/update', methods=['POST'])
@jwt_required()
def add_admin_update_to_request(request_id):
    """Add admin update to transition request"""
    try:
        current_user = User.query.get(get_jwt_identity())
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403

        transition_request = UserTransitionRequest.query.filter_by(id=request_id).first()
        if not transition_request:
            return jsonify({'error': 'Request not found'}), 404

        data = request.get_json() or {}
        update_text = (data.get('update_text') or '').strip()
        if not update_text:
            return jsonify({'error': 'Update text is required'}), 400

        update_type = data.get('update_type', 'admin_response')
        new_status = data.get('status')

        old_status = None
        if new_status and new_status != transition_request.status:
            old_status = transition_request.status
            transition_request.status = new_status
            transition_request.updated_at = datetime.utcnow()

            if new_status == 'completed':
                transition_request.completion_date = datetime.utcnow()

                is_privacy_compliant = (
                    not transition_request.new_occupant_first_name or
                    not transition_request.new_occupant_last_name or
                    not transition_request.new_occupant_type or
                    transition_request.new_occupant_type in ['', 'unknown', None]
                )
                if is_privacy_compliant:
                    if not transition_request.migration_completed:
                        return jsonify({
                            'error': 'Privacy-compliant requests must be completed via the Transition Linking interface.'
                        }), 400
                else:
                    migration_result = perform_user_migration(transition_request)
                    if not migration_result['success']:
                        current_app.logger.error(f"User migration failed: {migration_result['error']}")
                        return jsonify({'error': f"Migration failed: {migration_result['error']}"}), 500

        db.session.add(TransitionRequestUpdate(
            transition_request_id=request_id,
            user_id=current_user.id,
            update_text=update_text,
            update_type=update_type,
            old_status=old_status,
            new_status=new_status if old_status else None
        ))
        db.session.commit()

        return jsonify({
            'message': 'Update added successfully',
            'old_status': old_status,
            'new_status': new_status if old_status else transition_request.status
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding admin update: {str(e)}")
        return jsonify({'error': 'Failed to add update'}), 500


@transition_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_transition_stats():
    """Get transition request statistics (admin)"""
    try:
        current_user = User.query.get(get_jwt_identity())
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403

        status_counts = {s: UserTransitionRequest.query.filter_by(status=s).count()
                         for s in ['pending_review', 'in_progress', 'awaiting_docs', 'ready_for_transition', 'completed', 'cancelled']}

        priority_counts = {p: UserTransitionRequest.query.filter_by(priority=p).count()
                           for p in ['standard', 'urgent', 'emergency']}

        type_counts = {t: UserTransitionRequest.query.filter_by(request_type=t).count()
                       for t in ['owner_sale', 'tenant_moveout', 'owner_moving', 'other']}

        return jsonify({
            'status_counts': status_counts,
            'priority_counts': priority_counts,
            'type_counts': type_counts,
            'total_requests': UserTransitionRequest.query.count()
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching transition stats: {str(e)}")
        return jsonify({'error': 'Failed to fetch statistics'}), 500


@transition_bp.route('/admin/link-and-process', methods=['POST'])
@jwt_required()
def link_and_process_transition():
    """
    Link a transition request with a pending registration and process the transition.
    Privacy-compliant approach: current users provide only their data; new users register separately.
    """
    try:
        current_user = User.query.get(get_jwt_identity())
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403

        data = request.get_json() or {}
        transition_request_id = data.get('transition_request_id')
        registration_id = data.get('registration_id')
        new_user_data = data.get('new_user_data')
        if not all([transition_request_id, registration_id, new_user_data]):
            return jsonify({'error': 'Missing required data'}), 400

        transition_request = UserTransitionRequest.query.get(transition_request_id)
        if not transition_request:
            return jsonify({'error': 'Transition request not found'}), 404

        pending_registration = User.query.filter_by(id=registration_id, status='pending').first()
        if not pending_registration:
            return jsonify({'error': 'Pending registration not found'}), 404

        # Verify ERF matches
        pending_erf = None
        if pending_registration.resident:
            pending_erf = pending_registration.resident.erf_number
        elif pending_registration.owner:
            pending_erf = pending_registration.owner.erf_number
        if transition_request.erf_number != pending_erf:
            return jsonify({'error': f'ERF mismatch: request {transition_request.erf_number} vs registration {pending_erf}'}), 400

        current_user_leaving = User.query.get(transition_request.user_id)
        if not current_user_leaving:
            return jsonify({'error': 'Current user not found'}), 404

        result = perform_linked_migration(transition_request, current_user_leaving, pending_registration, new_user_data)
        if not result['success']:
            return jsonify({'error': result['error']}), 500

        # Finalize
        transition_request.status = 'completed'
        transition_request.migration_completed = True
        transition_request.migration_date = datetime.utcnow()
        transition_request.new_user_id = pending_registration.id

        db.session.add(TransitionRequestUpdate(
            transition_request_id=transition_request.id,
            user_id=current_user.id,
            update_text=f"Transition completed by linking with registration {registration_id}. {result['message']}",
            update_type='admin_note',
            old_status='in_progress',
            new_status='completed'
        ))
        db.session.commit()

        return jsonify({
            'message': 'Transition processed successfully',
            'transition_id': transition_request.id,
            'new_user_id': pending_registration.id,
            'migration_type': result.get('migration_type', 'linked_replacement')
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error linking and processing transition: {str(e)}")
        return jsonify({'error': f'Failed to process transition: {str(e)}'}), 500


def perform_linked_migration(transition_request, old_user, new_user, new_user_data):
    """
    Migration when linking a pending registration. Covers complete and partial replacements.
    """
    try:
        erf_number = transition_request.erf_number
        migration_date = datetime.utcnow()
        migration_reason = f'Linked transition {transition_request.id} with {new_user.email}'

        # Old user role composition
        old_is_resident = bool(old_user.resident and old_user.resident.status == 'active')
        old_is_owner = bool(old_user.owner and old_user.owner.status == 'active')
        old_role = 'owner_resident' if (old_is_owner and old_is_resident) else ('owner' if old_is_owner else ('resident' if old_is_resident else 'unknown'))

        intended_type = transition_request.new_occupant_type  # resident|owner|owner_resident|terminated

        if intended_type == 'resident':
            new_is_resident, new_is_owner = True, False
        elif intended_type == 'owner':
            new_is_resident, new_is_owner = False, True
        elif intended_type == 'owner_resident':
            new_is_resident, new_is_owner = True, True
        elif intended_type == 'terminated':
            new_is_resident, new_is_owner = False, False
        else:
            # Fallback to payload
            new_is_resident = bool(new_user_data.get('is_resident', False))
            new_is_owner = bool(new_user_data.get('is_owner', False))

        if new_is_resident and new_is_owner:
            new_role = 'owner_resident'
        elif new_is_owner:
            new_role = 'owner'
        elif new_is_resident:
            new_role = 'resident'
        elif intended_type == 'terminated':
            new_role = 'terminated'
        else:
            new_role = 'resident'

        if intended_type == 'terminated':
            # Pure termination (no new user)
            old_user.status = 'inactive'
            old_user.password_hash = 'DISABLED'
            if old_user.resident:
                old_user.resident.status = 'deleted_profile'
                old_user.resident.migration_date = migration_date
                old_user.resident.migration_reason = migration_reason
            if old_user.owner:
                old_user.owner.status = 'deleted_profile'
                old_user.owner.migration_date = migration_date
                old_user.owner.migration_reason = migration_reason

            old_vehicles = []
            if old_user.resident:
                old_vehicles += Vehicle.query.filter_by(resident_id=old_user.resident.id).all()
            if old_user.owner:
                old_vehicles += Vehicle.query.filter_by(owner_id=old_user.owner.id).all()
            for v in old_vehicles:
                v.status = 'inactive'
                v.migration_date = migration_date
                v.migration_reason = migration_reason

            transition_request.migration_completed = True
            transition_request.migration_date = migration_date
            transition_request.new_user_id = None
            transition_request.status = 'completed'

            db.session.commit()
            return {
                'success': True,
                'message': f'Terminated user access for ERF {erf_number}.',
                'migration_type': 'termination',
                'old_user_id': old_user.id,
                'old_user_status': 'inactive',
                'new_user_id': None,
                'vehicles_transferred': 0,
                'vehicles_deactivated': len(old_vehicles)
            }

        # Decide partial vs complete replacement
        is_partial_replacement = False
        old_keeps_owner = False
        old_keeps_resident = False

        if old_role == 'owner_resident':
            if new_role == 'resident':
                is_partial_replacement, old_keeps_owner = True, True
            elif new_role == 'owner':
                is_partial_replacement, old_keeps_resident = True, True

        if is_partial_replacement:
            # Old user stays active with the role they keep
            if old_keeps_owner:
                old_user.role = 'owner'
                if old_user.resident:
                    old_user.resident.status = 'deleted_profile'
                    old_user.resident.migration_date = migration_date
                    old_user.resident.migration_reason = migration_reason
            elif old_keeps_resident:
                old_user.role = 'resident'
                if old_user.owner:
                    old_user.owner.status = 'deleted_profile'
                    old_user.owner.migration_date = migration_date
                    old_user.owner.migration_reason = migration_reason
        else:
            # Complete replacement: old user loses everything
            old_user.status = 'inactive'
            old_user.password_hash = 'DISABLED'
            if old_user.resident:
                old_user.resident.status = 'deleted_profile'
                old_user.resident.migration_date = migration_date
                old_user.resident.migration_reason = migration_reason
            if old_user.owner:
                old_user.owner.status = 'deleted_profile'
                old_user.owner.migration_date = migration_date
                old_user.owner.migration_reason = migration_reason

            old_vehicles = []
            if old_user.resident:
                old_vehicles += Vehicle.query.filter_by(resident_id=old_user.resident.id).all()
            if old_user.owner:
                old_vehicles += Vehicle.query.filter_by(owner_id=old_user.owner.id).all()
            for v in old_vehicles:
                v.status = 'inactive'
                v.migration_date = migration_date
                v.migration_reason = migration_reason

        # Activate new user and (ensure) role records
        new_user.status = 'active'
        new_user.role = new_role

        if new_is_resident:
            if new_user.resident:
                new_user.resident.status = 'active'
                new_user.resident.erf_number = erf_number
                new_user.resident.intercom_code = 'ADMIN_SET_REQUIRED'
            else:
                db.session.add(Resident(
                    user_id=new_user.id,
                    first_name=new_user_data.get('first_name', ''),
                    last_name=new_user_data.get('last_name', ''),
                    erf_number=erf_number,
                    phone_number=new_user_data.get('phone_number', ''),
                    id_number=new_user_data.get('id_number', '999999999'),
                    street_number='1',
                    street_name='Main Street',
                    full_address=new_user_data.get('address', f'{erf_number} Main Street'),
                    intercom_code='ADMIN_SET_REQUIRED',
                    status='active'
                ))
        if new_is_owner:
            if new_user.owner:
                new_user.owner.status = 'active'
                new_user.owner.erf_number = erf_number
                new_user.owner.intercom_code = 'ADMIN_SET_REQUIRED'
            else:
                db.session.add(Owner(
                    user_id=new_user.id,
                    first_name=new_user_data.get('first_name', ''),
                    last_name=new_user_data.get('last_name', ''),
                    erf_number=erf_number,
                    phone_number=new_user_data.get('phone_number', ''),
                    id_number=new_user_data.get('id_number', '999999999'),
                    street_number='1',
                    street_name='Main Street',
                    full_address=new_user_data.get('address', f'{erf_number} Main Street'),
                    intercom_code='ADMIN_SET_REQUIRED',
                    title_deed_number='T000000',
                    postal_street_number='1',
                    postal_street_name='Main Street',
                    postal_suburb='Suburb',
                    postal_city='City',
                    postal_code='0000',
                    postal_province='Province',
                    full_postal_address='1 Main Street, Suburb, City, 0000',
                    status='active'
                ))

        # Finalize
        transition_request.migration_completed = True
        transition_request.migration_date = migration_date
        transition_request.new_user_id = new_user.id
        transition_request.status = 'completed'

        db.session.commit()

        vehicles_affected = 0 if is_partial_replacement else (len(old_vehicles) if not is_partial_replacement and 'old_vehicles' in locals() else 0)
        return {
            'success': True,
            'message': f'Migrated ERF {erf_number}: {old_role} → {new_role}',
            'migration_type': 'partial_replacement' if is_partial_replacement else 'complete_replacement',
            'old_user_id': old_user.id,
            'old_user_status': 'active' if is_partial_replacement else 'inactive',
            'new_user_id': new_user.id,
            'vehicles_transferred': 0,
            'vehicles_deactivated': vehicles_affected
        }
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': f'Linked migration failed: {str(e)}'}


@transition_bp.route('/admin/request/<request_id>/mark-migration-completed', methods=['PUT'])
@jwt_required()
def mark_transition_migration_completed(request_id):
    """Mark a transition request as migration completed (admin only)"""
    try:
        current_user = User.query.get(get_jwt_identity())
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403

        transition_request = UserTransitionRequest.query.get_or_404(request_id)
        transition_request.migration_completed = True
        transition_request.migration_date = datetime.utcnow()
        transition_request.updated_at = datetime.utcnow()

        db.session.add(TransitionRequestUpdate(
            transition_request_id=request_id,
            user_id=current_user.id,
            update_text="Migration manually marked as completed after successful transition linking",
            update_type='admin_note'
        ))
        db.session.commit()

        return jsonify({
            'message': 'Transition request marked as migration completed',
            'migration_completed': True,
            'migration_date': transition_request.migration_date.isoformat()
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error marking transition as migration completed: {str(e)}")
        return jsonify({'error': 'Failed to mark migration as completed'}), 500


def handle_user_termination(transition_request):
    """
    Handle user termination/exit from the estate. Deactivates user and vehicles.
    """
    try:
        user = User.query.get(transition_request.user_id)
        if not user:
            return {'success': False, 'error': 'User not found'}

        erf_number = transition_request.erf_number

        user.status = 'inactive'
        if user.resident:
            user.resident.status = 'inactive'
            user.resident.migration_date = datetime.utcnow()
            user.resident.migration_reason = f'User terminated from ERF {erf_number}'
        if user.owner:
            user.owner.status = 'inactive'
            user.owner.migration_date = datetime.utcnow()
            user.owner.migration_reason = f'User terminated from ERF {erf_number}'

        vehicles = []
        if user.resident:
            vehicles += Vehicle.query.filter_by(resident_id=user.resident.id).all()
        if user.owner:
            vehicles += Vehicle.query.filter_by(owner_id=user.owner.id).all()
        for v in vehicles:
            v.status = 'terminated'
            v.migration_date = datetime.utcnow()
            v.migration_reason = f'User terminated from ERF {erf_number}'

        # Log
        user_name = "Unknown User"
        if user.resident:
            user_name = f"{user.resident.first_name} {user.resident.last_name}"
        elif user.owner:
            user_name = f"{user.owner.first_name} {user.owner.last_name}"
        elif getattr(user, 'full_name', None):
            user_name = user.full_name

        log_user_change(
            user.id, user_name, erf_number,
            'transition_termination', 'user_status', 'active', 'terminated'
        )

        transition_request.migration_completed = True
        transition_request.migration_date = datetime.utcnow()

        db.session.add(TransitionRequestUpdate(
            transition_request_id=transition_request.id,
            user_id=transition_request.user_id,
            update_text=f"User terminated and removed from ERF {erf_number}. All access revoked.",
            update_type='termination'
        ))
        db.session.commit()

        return {'success': True, 'message': f'User terminated for ERF {erf_number}', 'user_id': user.id, 'erf_number': erf_number}
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error handling user termination: {str(e)}")
        return {'success': False, 'error': f'Termination failed: {str(e)}'}


def find_pending_user_for_erf(erf_number):
    """
    Find a pending user registration for the specified ERF number.
    """
    try:
        # Check pending residents
        for r in Resident.query.filter_by(erf_number=erf_number).all():
            if r.user and r.user.status == 'pending':
                return r.user

        # Check pending owners
        for o in Owner.query.filter_by(erf_number=erf_number).all():
            if o.user and o.user.status == 'pending':
                return o.user

        return None
    except Exception as e:
        current_app.logger.error(f"Error finding pending user for ERF {erf_number}: {str(e)}")
        return None


def handle_transition_linking(transition_request, new_user):
    """
    Link a transition request with a new user (activate new, deactivate old, log changes).
    Use this only from the dedicated linking interface (not status endpoint).
    """
    try:
        old_user = User.query.get(transition_request.user_id)
        if not old_user:
            return {'success': False, 'error': 'Old user not found'}

        erf_number = transition_request.erf_number

        # Activate new → pending -> active
        new_user.status = 'active'

        # Deactivate old
        old_user.status = 'inactive'

        migration_reason = f'Transitioned to {new_user.email} via transition {transition_request.id}'
        now = datetime.utcnow()

        if old_user.resident:
            old_user.resident.status = 'migrated'
            old_user.resident.migration_date = now
            old_user.resident.migration_reason = migration_reason
        if old_user.owner:
            old_user.owner.status = 'migrated'
            old_user.owner.migration_date = now
            old_user.owner.migration_reason = migration_reason

        vehicles = []
        if old_user.resident:
            vehicles += Vehicle.query.filter_by(resident_id=old_user.resident.id).all()
        if old_user.owner:
            vehicles += Vehicle.query.filter_by(owner_id=old_user.owner.id).all()
        for v in vehicles:
            v.status = 'transferred'
            v.migration_date = now
            v.migration_reason = f'Owner transitioned from {old_user.email} to {new_user.email}'

        old_user_name = "Unknown User"
        if old_user.resident:
            old_user_name = f"{old_user.resident.first_name} {old_user.resident.last_name}"
        elif old_user.owner:
            old_user_name = f"{old_user.owner.first_name} {old_user.owner.last_name}"

        new_user_name = "Unknown User"
        if new_user.resident:
            new_user_name = f"{new_user.resident.first_name} {new_user.resident.last_name}"
        elif new_user.owner:
            new_user_name = f"{new_user.owner.first_name} {new_user.owner.last_name}"

        log_user_change(new_user.id, new_user_name, erf_number, 'transition_linking', 'user_status', 'pending', 'active')
        log_user_change(old_user.id, old_user_name, erf_number, 'transition_linking', 'user_status', 'active', 'inactive')

        transition_request.migration_completed = True
        transition_request.migration_date = now

        db.session.add(TransitionRequestUpdate(
            transition_request_id=transition_request.id,
            user_id=transition_request.user_id,
            update_text=f"Transition linking completed: {old_user_name} → {new_user_name} for ERF {erf_number}. Old user removed from gate register, new user activated.",
            update_type='linking_completed'
        ))
        db.session.commit()

        return {
            'success': True,
            'message': f'Linking completed: {old_user_name} → {new_user_name} for ERF {erf_number}.',
            'old_user_id': old_user.id,
            'new_user_id': new_user.id,
            'erf_number': erf_number
        }
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error handling transition linking: {str(e)}")
        return {'success': False, 'error': f'Linking failed: {str(e)}'}
