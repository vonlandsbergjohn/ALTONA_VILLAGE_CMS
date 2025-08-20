
# --- NEW ADMIN ENDPOINT: Find and Link Transition Requests for Same ERF (Owner <-> Tenant) ---
@transition_bp.route('/admin/link-existing-requests', methods=['POST'])
@jwt_required()
def link_existing_transition_requests():
    """Link two existing transition requests for the same ERF (owner and tenant), process migration, and update statuses."""
    current_user = User.query.get(get_jwt_identity())
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    owner_request_id = data.get('owner_request_id')
    tenant_request_id = data.get('tenant_request_id')

    if not owner_request_id or not tenant_request_id:
        return jsonify({'error': 'Both request IDs are required'}), 400

    owner_request = UserTransitionRequest.query.get(owner_request_id)
    tenant_request = UserTransitionRequest.query.get(tenant_request_id)

    if not owner_request or not tenant_request:
        return jsonify({'error': 'One or both transition requests not found'}), 404

    # Check both requests are for the same ERF and not completed
    if owner_request.erf_number != tenant_request.erf_number:
        return jsonify({'error': 'Transition requests are for different ERFs'}), 400
    if owner_request.status == 'completed' or tenant_request.status == 'completed':
        return jsonify({'error': 'One or both transition requests are already completed'}), 400

    # Check roles
    owner_user = User.query.get(owner_request.user_id)
    tenant_user = User.query.get(tenant_request.user_id)
    if not owner_user or not tenant_user:
        return jsonify({'error': 'One or both users not found'}), 404

    # Owner must be owner, tenant must be resident/tenant
    owner_is_owner = Owner.query.filter_by(user_id=owner_user.id, erf_number=owner_request.erf_number).first() is not None
    tenant_is_resident = Resident.query.filter_by(user_id=tenant_user.id, erf_number=tenant_request.erf_number).first() is not None
    if not owner_is_owner or not tenant_is_resident:
        return jsonify({'error': 'Role mismatch: owner/tenant records not found for ERF'}), 400

    # Process migration: make tenant the new owner-resident, deactivate seller
    try:
        # Deactivate seller (owner)
        owner_user.status = 'inactive'
        owner_request.status = 'completed'
        owner_request.completed_at = datetime.utcnow()

        # Update tenant to owner-resident
        tenant_user.role = 'owner_resident'
        tenant_request.status = 'completed'
        tenant_request.completed_at = datetime.utcnow()

        # Update Resident and Owner tables
        # Remove old owner record
        Owner.query.filter_by(user_id=owner_user.id, erf_number=owner_request.erf_number).delete()
        # Add new owner record for tenant
        new_owner = Owner(user_id=tenant_user.id, erf_number=tenant_request.erf_number, first_name=tenant_user.first_name, last_name=tenant_user.last_name, phone_number=tenant_user.phone_number)
        db.session.add(new_owner)

        # Optionally update Resident record for tenant (set is_owner=True)
        resident_record = Resident.query.filter_by(user_id=tenant_user.id, erf_number=tenant_request.erf_number).first()
        if resident_record:
            resident_record.is_owner = True

        db.session.commit()
        return jsonify({'success': True, 'message': 'Transition requests linked and migration processed.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to process migration: {str(e)}'}), 500
"""
User Transition Request API Routes
Handles property move-out, sales, and tenant changes
Following the same pattern as the complaint system
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.user import db, User, Resident, Owner, UserTransitionRequest, TransitionRequestUpdate, TransitionVehicle, Vehicle
from ..routes.admin_notifications import log_user_change
from datetime import datetime, date
import uuid

transition_bp = Blueprint('transition', __name__)

def perform_user_migration(transition_request):
    """
    Comprehensive user migration system that handles all transition scenarios:
    
    SCENARIO 1: Complete User Replacement (Different People)
    - Owner sells to new owner → Old user deactivated, new user created
    - Tenant moves out, new tenant moves in → Old user deactivated, new user created
    
    SCENARIO 2: Role Change (Same Person)  
    - Owner becomes owner-resident (moves into property) → Same user, add resident role
    - Owner-resident becomes owner only (moves out) → Same user, remove resident role
    
    SCENARIO 3: Partial Replacement
    - Owner moves in, tenant moves out → Tenant deactivated, owner gets resident role
    
    Key Logic:
    - Check if new occupant email matches existing user → Role change scenario 
    - Check if new occupant is different person → User replacement scenario
    - Handle password preservation for same-person transitions
    - Handle complete deactivation for different-person transitions
    """
    try:
        # Validate transition request data
        if (not transition_request.new_occupant_type or 
            transition_request.new_occupant_type == 'unknown' or
            not transition_request.new_occupant_first_name or
            not transition_request.new_occupant_last_name):
            return {'success': True, 'message': 'No new occupant data to migrate'}
        
        # Get the current user (person requesting the transition)
        current_user = User.query.get(transition_request.user_id)
        if not current_user:
            return {'success': False, 'error': 'Current user not found'}
        
        # Get new occupant email (this determines if it's same person or different person)
        new_occupant_email = transition_request.new_occupant_email
        if not new_occupant_email:
            new_occupant_email = f"temp_{transition_request.new_occupant_first_name.lower()}_{transition_request.new_occupant_last_name.lower()}@altona-village.temp"
        
        # 🔍 DETERMINE MIGRATION SCENARIO
        is_same_person = (current_user.email == new_occupant_email)
        existing_new_user = User.query.filter_by(email=new_occupant_email).first() if not is_same_person else None
        
        print(f"🔄 Migration Analysis:")
        print(f"   Current user: {current_user.email} (Role: {current_user.role})")
        print(f"   New occupant: {new_occupant_email}")
        print(f"   Same person: {is_same_person}")
        print(f"   New occupant type: {transition_request.new_occupant_type}")
        
        # 📋 SCENARIO DETECTION AND EXECUTION
        
        if is_same_person:
            # SCENARIO 2: ROLE CHANGE (Same Person)
            return handle_role_change_migration(transition_request, current_user)
        
        elif existing_new_user:
            # SCENARIO 3: PARTIAL REPLACEMENT (Existing user gets new role)
            return handle_partial_replacement_migration(transition_request, current_user, existing_new_user)
        
        else:
            # SCENARIO 1: COMPLETE USER REPLACEMENT (Different People)
            return handle_complete_user_replacement(transition_request, current_user, new_occupant_email)
        
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': f'Migration failed: {str(e)}'}


def handle_role_change_migration(transition_request, current_user):
    """
    SCENARIO 2: Same person changing roles
    Example: Owner becomes owner-resident (moves into property)
    - Keep same user account and password
    - Add/modify resident/owner records as needed
    - Update role in user table
    """
    try:
        print(f"🏠 ROLE CHANGE MIGRATION: {current_user.email}")
        
        erf_number = transition_request.erf_number
        new_type = transition_request.new_occupant_type
        
        # Update user role based on new occupant type
        if new_type == 'new_tenant':
            current_user.role = 'resident'
        elif new_type == 'new_owner':
            current_user.role = 'owner'  
        elif new_type == 'owner_resident':
            current_user.role = 'owner_resident'
        
        # Handle resident record
        existing_resident = current_user.resident
        if new_type in ['new_tenant', 'owner_resident']:
            if not existing_resident:
                # Create new resident record
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
                print(f"   ✅ Created new resident record for ERF {erf_number}")
            else:
                # Update existing resident record
                existing_resident.status = 'active'
                existing_resident.erf_number = erf_number
                print(f"   ✅ Updated existing resident record for ERF {erf_number}")
        else:
            # Remove resident role if not needed
            if existing_resident:
                existing_resident.status = 'inactive'
                print(f"   📝 Deactivated resident record (owner-only now)")
        
        # Handle owner record  
        existing_owner = current_user.owner
        if new_type in ['new_owner', 'owner_resident']:
            if not existing_owner:
                # Create new owner record
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
                    full_postal_address=transition_request.new_occupant_full_postal_address or f'1 Main Street, Suburb, City, 0000',
                    status='active'
                )
                db.session.add(new_owner)
                print(f"   ✅ Created new owner record for ERF {erf_number}")
            else:
                # Update existing owner record
                existing_owner.status = 'active'
                existing_owner.erf_number = erf_number
                print(f"   ✅ Updated existing owner record for ERF {erf_number}")
        else:
            # Remove owner role if not needed
            if existing_owner:
                existing_owner.status = 'inactive' 
                print(f"   📝 Deactivated owner record (resident-only now)")
        
        # Record migration
        transition_request.migration_completed = True
        transition_request.migration_date = datetime.utcnow()
        transition_request.new_user_id = current_user.id
        
        db.session.commit()
        
        return {
            'success': True,
            'message': f'Role change completed: {current_user.email} is now {current_user.role} for ERF {erf_number}',
            'migration_type': 'role_change',
            'user_id': current_user.id,
            'password_preserved': True
        }
        
    except Exception as e:
        db.session.rollback()
        raise e


def handle_partial_replacement_migration(transition_request, old_user, new_user):
    """
    SCENARIO 3: Partial replacement - existing user gets additional role
    Example: Owner (existing user) moves in, tenant (old user) moves out
    - Deactivate old user completely
    - Give existing new user the additional role for this ERF
    """
    try:
        print(f"🔄 PARTIAL REPLACEMENT: {old_user.email} → {new_user.email}")
        
        # Step 1: Deactivate old user completely
        old_user.status = 'inactive'
        old_user.password_hash = 'DISABLED'
        print(f"   ❌ Deactivated old user: {old_user.email}")
        
        # Step 2: Mark old user's records as deleted_profile
        erf_number = transition_request.erf_number
        migration_reason = f'Replaced by existing user {new_user.email} via transition {transition_request.id}'
        
        if old_user.resident:
            old_user.resident.status = 'deleted_profile'
            old_user.resident.migration_date = datetime.utcnow()
            old_user.resident.migration_reason = migration_reason
        
        if old_user.owner:
            old_user.owner.status = 'deleted_profile'
            old_user.owner.migration_date = datetime.utcnow()
            old_user.owner.migration_reason = migration_reason
        
        # Step 3: Add new role to existing user
        new_type = transition_request.new_occupant_type
        
        if new_type in ['new_tenant', 'owner_resident'] and not new_user.resident:
            # Add resident record to existing user
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
            print(f"   ✅ Added resident role to {new_user.email} for ERF {erf_number}")
        
        if new_type in ['new_owner', 'owner_resident'] and not new_user.owner:
            # Add owner record to existing user
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
                full_postal_address=transition_request.new_occupant_full_postal_address or f'1 Main Street, Suburb, City, 0000',
                status='active'
            )
            db.session.add(new_owner)
            print(f"   ✅ Added owner role to {new_user.email} for ERF {erf_number}")
        
        # Update new user's role
        if new_type == 'owner_resident':
            new_user.role = 'owner_resident'
        elif new_type == 'new_owner' and new_user.role != 'owner_resident':
            new_user.role = 'owner'
        elif new_type == 'new_tenant' and new_user.role != 'owner_resident':
            new_user.role = 'resident'
        
        # Record migration
        transition_request.migration_completed = True
        transition_request.migration_date = datetime.utcnow()
        transition_request.new_user_id = new_user.id
        
        db.session.commit()
        
        return {
            'success': True,
            'message': f'Partial replacement completed: {old_user.email} deactivated, {new_user.email} now has access to ERF {erf_number}',
            'migration_type': 'partial_replacement',
            'old_user_id': old_user.id,
            'new_user_id': new_user.id
        }
        
    except Exception as e:
        db.session.rollback()
        raise e


def handle_complete_user_replacement(transition_request, old_user, new_email):
    """
    SCENARIO 1: Complete user replacement - different people
    Example: Owner sells property to completely new owner
    - Completely deactivate old user (disable password, mark as deleted_profile)
    - Create brand new user account for new person
    """
    try:
        print(f"🔄 COMPLETE USER REPLACEMENT: {old_user.email} → {new_email}")
        
        # Step 1: Completely deactivate old user
        old_user.status = 'inactive'
        old_user.password_hash = 'DISABLED'  # Disable login completely
        print(f"   ❌ Deactivated old user: {old_user.email}")
        
        # Step 2: Mark all old user's records as deleted_profile for audit trail
        erf_number = transition_request.erf_number
        migration_reason = f'Replaced by new user {new_email} via transition {transition_request.id}'
        migration_date = datetime.utcnow()
        
        if old_user.resident:
            old_user.resident.status = 'deleted_profile'
            old_user.resident.migration_date = migration_date
            old_user.resident.migration_reason = migration_reason
            print(f"   📝 Marked old resident record as deleted_profile")
        
        if old_user.owner:
            old_user.owner.status = 'deleted_profile'
            old_user.owner.migration_date = migration_date
            old_user.owner.migration_reason = migration_reason
            print(f"   📝 Marked old owner record as deleted_profile")
        
        # Step 3: Deactivate old vehicles
        old_vehicles = []
        if old_user.resident:
            old_vehicles.extend(Vehicle.query.filter_by(resident_id=old_user.resident.id).all())
        if old_user.owner:
            old_vehicles.extend(Vehicle.query.filter_by(owner_id=old_user.owner.id).all())
        
        for vehicle in old_vehicles:
            vehicle.status = 'inactive'
            vehicle.migration_date = migration_date
            vehicle.migration_reason = migration_reason
            print(f"   🚗 Deactivated vehicle: {vehicle.registration_number}")
        
        # Step 4: Create completely new user account
        from werkzeug.security import generate_password_hash
        temp_password = 'test'  # Default password
        
        new_user = User(
            email=new_email,
            password_hash=generate_password_hash(temp_password),
            role='resident',  # Will be updated based on occupant type
            status='active'
        )
        db.session.add(new_user)
        db.session.flush()  # Get new_user.id
        print(f"   ✅ Created new user: {new_email}")
        
        # Step 5: Create new records based on occupant type
        new_type = transition_request.new_occupant_type
        new_resident = None
        new_owner = None
        
        if new_type == 'new_tenant':
            new_user.role = 'resident'
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
            print(f"   🏠 Created resident record for ERF {erf_number}")
            
        elif new_type == 'new_owner':
            new_user.role = 'owner'
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
                full_postal_address=transition_request.new_occupant_full_postal_address or f'1 Main Street, Suburb, City, 0000',
                status='active'
            )
            db.session.add(new_owner)
            print(f"   🏠 Created owner record for ERF {erf_number}")
            
        elif new_type == 'owner_resident':
            new_user.role = 'owner_resident'
            # Create both resident and owner records
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
                full_postal_address=transition_request.new_occupant_full_postal_address or f'1 Main Street, Suburb, City, 0000',
                status='active'
            )
            db.session.add(new_owner)
            print(f"   🏠 Created owner-resident records for ERF {erf_number}")
        
        # Step 6: Vehicle handling - DO NOT TRANSFER vehicles to new users
        # Vehicles remain deactivated with the old user as they are personal property
        print(f"   🚗 Vehicles remain deactivated with old user (not transferred)")
        
        # Step 7: Record migration completion
        transition_request.migration_completed = True
        transition_request.migration_date = migration_date
        transition_request.new_user_id = new_user.id
        
        db.session.commit()
        
        return {
            'success': True,
            'message': f'Complete user replacement: {old_user.email} deactivated, new user {new_email} created (password: {temp_password})',
            'migration_type': 'complete_replacement',
            'old_user_id': old_user.id,
            'new_user_id': new_user.id,
            'new_password': temp_password
        }
        
    except Exception as e:
        db.session.rollback()
        raise e


@transition_bp.route('/request', methods=['POST'])
@jwt_required()
def create_transition_request():
    """Create a new user transition request"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['erf_number', 'request_type', 'current_role', 'new_occupant_type']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate request type
        valid_request_types = ['owner_sale', 'tenant_moveout', 'owner_moving', 'other']
        if data['request_type'] not in valid_request_types:
            return jsonify({'error': 'Invalid request type'}), 400
        
        # Validate new occupant type (future residency status)
        valid_occupant_types = ['resident', 'owner', 'owner_resident', 'terminated']
        if data['new_occupant_type'] not in valid_occupant_types:
            return jsonify({'error': 'Invalid future residency status'}), 400
        
        # Validate current role
        valid_roles = ['owner', 'tenant', 'owner_resident']
        if data['current_role'] not in valid_roles:
            return jsonify({'error': 'Invalid current role'}), 400
        
        # Create new transition request
        transition_request = UserTransitionRequest(
            user_id=current_user_id,
            erf_number=data['erf_number'],
            request_type=data['request_type'],
            current_role=data['current_role']
        )
        
        # Set optional timeline fields
        date_fields = [
            'intended_moveout_date', 'property_transfer_date', 'new_occupant_movein_date',
            'expected_transfer_date', 'lease_end_date', 'rental_start_date'
        ]
        
        for field in date_fields:
            if field in data and data[field]:
                try:
                    setattr(transition_request, field, datetime.strptime(data[field], '%Y-%m-%d').date())
                except ValueError:
                    return jsonify({'error': f'Invalid date format for {field}. Use YYYY-MM-DD'}), 400
        
        # Set text fields
        text_fields = [
            'notice_period', 'transfer_attorney', 'moveout_reason', 'moveout_reason_other',
            'property_management_company', 'outstanding_matters_other', 'new_occupant_type',
            'new_occupant_name', 'new_occupant_phone', 'new_occupant_email',
            'access_handover_requirements', 'property_condition_notes', 'community_introduction_needs'
        ]
        
        for field in text_fields:
            if field in data:
                setattr(transition_request, field, data.get(field))
        
        # Set boolean fields
        boolean_fields = [
            'sale_agreement_signed', 'new_owner_details_known', 'deposit_return_required',
            'new_tenant_selected', 'gate_access_transfer', 'intercom_access_transfer',
            'vehicle_registration_transfer', 'visitor_access_transfer', 'community_notifications_transfer',
            'unpaid_levies', 'pending_maintenance', 'community_violations'
        ]
        
        for field in boolean_fields:
            if field in data:
                setattr(transition_request, field, bool(data.get(field)))
        
        # Set integer fields
        integer_fields = ['new_occupant_adults', 'new_occupant_children', 'new_occupant_pets']
        for field in integer_fields:
            if field in data and data[field] is not None and data[field] != '':
                try:
                    setattr(transition_request, field, int(data.get(field)))
                except (ValueError, TypeError):
                    # If conversion fails, set to None or 0
                    setattr(transition_request, field, 0)
        
        # Set priority based on notice period
        if 'intended_moveout_date' in data and data['intended_moveout_date']:
            moveout_date = datetime.strptime(data['intended_moveout_date'], '%Y-%m-%d').date()
            days_notice = (moveout_date - date.today()).days
            
            if days_notice < 7:
                transition_request.priority = 'emergency'
            elif days_notice < 30:
                transition_request.priority = 'urgent'
            else:
                transition_request.priority = 'standard'
        
        db.session.add(transition_request)
        db.session.flush()  # Get the ID
        
        # Add vehicle information if provided
        if 'vehicles' in data and isinstance(data['vehicles'], list):
            for vehicle_data in data['vehicles']:
                if vehicle_data.get('license_plate'):
                    vehicle = TransitionVehicle(
                        transition_request_id=transition_request.id,
                        vehicle_make=vehicle_data.get('vehicle_make'),
                        vehicle_model=vehicle_data.get('vehicle_model'),
                        license_plate=vehicle_data.get('license_plate'),
                        color=vehicle_data.get('color')
                    )
                    db.session.add(vehicle)
        
        # Create initial update
        initial_update = TransitionRequestUpdate(
            transition_request_id=transition_request.id,
            user_id=current_user_id,
            update_text=f"Transition request submitted for ERF {data['erf_number']} - {data['request_type'].replace('_', ' ').title()}",
            update_type='comment'
        )
        db.session.add(initial_update)
        
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
        
        requests = UserTransitionRequest.query.filter_by(user_id=current_user_id).order_by(
            UserTransitionRequest.created_at.desc()
        ).all()
        
        return jsonify({
            'requests': [req.to_dict() for req in requests]
        }), 200
        
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
        
        # Check if user owns this request or is admin
        if transition_request.user_id != current_user.id and current_user.role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        # Get request details with updates and vehicles
        request_data = transition_request.to_dict()
        
        # Add updates
        updates = TransitionRequestUpdate.query.filter_by(
            transition_request_id=request_id
        ).order_by(TransitionRequestUpdate.created_at.desc()).all()
        
        request_data['updates'] = [update.to_dict() for update in updates]
        
        # Add vehicles
        vehicles = TransitionVehicle.query.filter_by(
            transition_request_id=request_id
        ).all()
        
        request_data['vehicles'] = [vehicle.to_dict() for vehicle in vehicles]
        
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
        data = request.get_json()
        
        if not data.get('update_text'):
            return jsonify({'error': 'Update text is required'}), 400
        
        transition_request = UserTransitionRequest.query.get_or_404(request_id)
        
        # Check access permissions
        current_user = User.query.get(current_user_id)
        if transition_request.user_id != current_user_id and current_user.role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        # Create update
        update = TransitionRequestUpdate(
            transition_request_id=request_id,
            user_id=current_user_id,
            update_text=data['update_text'],
            update_type=data.get('update_type', 'comment')
        )
        
        db.session.add(update)
        
        # Update the request's updated_at timestamp
        transition_request.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Update added successfully',
            'update': update.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding transition request update: {str(e)}")
        return jsonify({'error': 'Failed to add update'}), 500

# Admin routes
@transition_bp.route('/admin/requests', methods=['GET'])
@jwt_required()
def get_all_transition_requests():
    """Get all transition requests (admin only)"""
    try:
        current_user = User.query.get(get_jwt_identity())
        
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        # Get filter parameters
        status_filter = request.args.get('status')
        priority_filter = request.args.get('priority')
        erf_filter = request.args.get('erf_number')
        
        # Build query
        query = UserTransitionRequest.query
        
        if status_filter:
            query = query.filter(UserTransitionRequest.status == status_filter)
        if priority_filter:
            query = query.filter(UserTransitionRequest.priority == priority_filter)
        if erf_filter:
            query = query.filter(UserTransitionRequest.erf_number.contains(erf_filter))
        
        requests = query.order_by(
            UserTransitionRequest.priority.desc(),
            UserTransitionRequest.created_at.desc()
        ).all()
        
        return jsonify({
            'requests': [req.to_dict() for req in requests],
            'total': len(requests)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching admin transition requests: {str(e)}")
        return jsonify({'error': 'Failed to fetch requests'}), 500

@transition_bp.route('/admin/request/<request_id>', methods=['GET'])
@jwt_required()
def get_admin_transition_request_details(request_id):
    """Get detailed transition request information for admin"""
    try:
        current_user = User.query.get(get_jwt_identity())
        
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        request = UserTransitionRequest.query.filter_by(id=request_id).first()
        
        if not request:
            return jsonify({'error': 'Request not found'}), 404
        
        # Get associated updates
        updates = TransitionRequestUpdate.query.filter_by(
            transition_request_id=request_id
        ).order_by(TransitionRequestUpdate.created_at.desc()).all()
        
        # Get associated vehicles
        vehicles = TransitionVehicle.query.filter_by(
            transition_request_id=request_id
        ).all()
        
        request_data = request.to_dict()
        request_data['updates'] = [update.to_dict() for update in updates]
        request_data['vehicles'] = [vehicle.to_dict() for vehicle in vehicles]
        
        return jsonify(request_data), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching admin transition request details: {str(e)}")
        return jsonify({'error': 'Failed to fetch request details'}), 500

@transition_bp.route('/admin/request/<request_id>/assign', methods=['PUT'])
@jwt_required()
def assign_transition_request(request_id):
    """Assign transition request to admin"""
    try:
        current_user = User.query.get(get_jwt_identity())
        
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        transition_request = UserTransitionRequest.query.get_or_404(request_id)
        data = request.get_json()
        
        # Assign to admin (can be self-assignment)
        admin_id = data.get('admin_id', current_user.id)
        
        # Verify admin exists
        admin_user = User.query.get(admin_id)
        if not admin_user or admin_user.role != 'admin':
            return jsonify({'error': 'Invalid admin ID'}), 400
        
        old_admin = transition_request.assigned_admin
        transition_request.assigned_admin = admin_id
        transition_request.updated_at = datetime.utcnow()
        
        # Create update record
        update_text = f"Request assigned to {admin_user.get_full_name()}"
        if old_admin:
            old_admin_user = User.query.get(old_admin)
            update_text = f"Request reassigned from {old_admin_user.get_full_name() if old_admin_user else 'Unknown'} to {admin_user.get_full_name()}"
        
        update = TransitionRequestUpdate(
            transition_request_id=request_id,
            user_id=current_user.id,
            update_text=update_text,
            update_type='admin_note'
        )
        
        db.session.add(update)
        db.session.commit()
        
        return jsonify({
            'message': 'Request assigned successfully',
            'assigned_to': admin_user.get_full_name()
        }), 200
        
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
        
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        transition_request = UserTransitionRequest.query.get_or_404(request_id)
        data = request.get_json()
        
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
        
        # Set completion date if completed
        if new_status == 'completed':
            transition_request.completion_date = datetime.utcnow()
            
            # Check if this is a termination/exit (no new occupant)
            is_termination = (
                transition_request.new_occupant_type == 'terminated' or
                transition_request.request_type == 'exit' or
                (transition_request.new_occupant_type in ['', 'unknown', None] and 
                 not transition_request.new_occupant_first_name)
            )
            
            # Check if this is a privacy-compliant transition request (no new occupant data)
            is_privacy_compliant = (
                not transition_request.new_occupant_first_name or 
                transition_request.new_occupant_first_name.strip() == '' or
                not transition_request.new_occupant_last_name or 
                transition_request.new_occupant_last_name.strip() == '' or
                not transition_request.new_occupant_type or
                transition_request.new_occupant_type in ['', 'unknown', None]
            )
            
            if is_termination:
                # For termination requests, only terminate if no linking has been completed
                if not transition_request.migration_completed:
                    # Check if there's a pending user that could be linked
                    pending_user = find_pending_user_for_erf(transition_request.erf_number)
                    
                    if pending_user:
                        # There's a pending user - don't terminate yet, must use linking interface
                        return jsonify({
                            'error': f'Found pending user for ERF {transition_request.erf_number}. Please use the Transition Linking interface to complete this transition instead of marking as completed directly.'
                        }), 400
                    else:
                        # No pending user found - safe to terminate
                        termination_result = handle_user_termination(transition_request)
                        if not termination_result['success']:
                            current_app.logger.error(f"User termination failed: {termination_result['error']}")
                            return jsonify({'error': f'Termination failed: {termination_result["error"]}'}), 500
                        
                        # Mark migration as completed for terminations
                        transition_request.migration_completed = True
                # If already migration_completed, just update the status (linking was already done)
                
            elif is_privacy_compliant:
                # Privacy-compliant transitions must be completed via the linking interface
                if not transition_request.migration_completed:
                    return jsonify({
                        'error': 'This privacy-compliant transition request must be completed using the Transition Linking interface. The new occupant should register separately, then use the linking feature to complete the transition.'
                    }), 400
            else:
                # Legacy transition with new occupant data - use old migration method
                migration_result = perform_user_migration(transition_request)
                if not migration_result['success']:
                    current_app.logger.error(f"User migration failed: {migration_result['error']}")
                    return jsonify({'error': f'Migration failed: {migration_result["error"]}'}), 500
        
        # Create status update record
        update = TransitionRequestUpdate(
            transition_request_id=request_id,
            user_id=current_user.id,
            update_text=data.get('update_message', f"Status changed from {old_status} to {new_status}"),
            update_type='status_change',
            old_status=old_status,
            new_status=new_status
        )
        
        db.session.add(update)
        db.session.commit()
        
        return jsonify({
            'message': 'Status updated successfully',
            'old_status': old_status,
            'new_status': new_status
        }), 200
        
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
        
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        transition_request = UserTransitionRequest.query.filter_by(id=request_id).first()
        
        if not transition_request:
            return jsonify({'error': 'Request not found'}), 404
        
        data = request.get_json()
        update_text = data.get('update_text', '').strip()
        update_type = data.get('update_type', 'admin_response')
        new_status = data.get('status')  # Optional status change
        
        if not update_text:
            return jsonify({'error': 'Update text is required'}), 400
        
        # Handle status change if provided
        old_status = None
        if new_status and new_status != transition_request.status:
            old_status = transition_request.status
            transition_request.status = new_status
            transition_request.updated_at = datetime.utcnow()
            
            # Set completion date if status is completed
            if new_status == 'completed':
                transition_request.completion_date = datetime.utcnow()
                
                # Check if this is a privacy-compliant transition request (no new occupant data)
                is_privacy_compliant = (
                    not transition_request.new_occupant_first_name or 
                    transition_request.new_occupant_first_name.strip() == '' or
                    not transition_request.new_occupant_last_name or 
                    transition_request.new_occupant_last_name.strip() == '' or
                    not transition_request.new_occupant_type or
                    transition_request.new_occupant_type in ['', 'unknown', None]
                )
                
                if is_privacy_compliant:
                    # Privacy-compliant transitions must be completed via the linking interface
                    if not transition_request.migration_completed:
                        return jsonify({
                            'error': 'This privacy-compliant transition request must be completed using the Transition Linking interface. The new occupant should register separately, then use the linking feature to complete the transition.'
                        }), 400
                else:
                    # Legacy transition with new occupant data - use old migration method
                    migration_result = perform_user_migration(transition_request)
                    if not migration_result['success']:
                        current_app.logger.error(f"User migration failed: {migration_result['error']}")
                        return jsonify({'error': f'Migration failed: {migration_result["error"]}'}), 500
        
        # Create the update
        update = TransitionRequestUpdate(
            transition_request_id=request_id,
            user_id=current_user.id,
            update_text=update_text,
            update_type=update_type,
            old_status=old_status,
            new_status=new_status if old_status else None
        )
        
        db.session.add(update)
        db.session.commit()
        
        return jsonify({
            'message': 'Update added successfully',
            'update': update.to_dict(),
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
    """Get transition request statistics"""
    try:
        current_user = User.query.get(get_jwt_identity())
        
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        # Get counts by status
        status_counts = {}
        for status in ['pending_review', 'in_progress', 'awaiting_docs', 'ready_for_transition', 'completed', 'cancelled']:
            count = UserTransitionRequest.query.filter_by(status=status).count()
            status_counts[status] = count
        
        # Get counts by priority
        priority_counts = {}
        for priority in ['standard', 'urgent', 'emergency']:
            count = UserTransitionRequest.query.filter_by(priority=priority).count()
            priority_counts[priority] = count
        
        # Get counts by request type
        type_counts = {}
        for req_type in ['owner_sale', 'tenant_moveout', 'owner_moving', 'other']:
            count = UserTransitionRequest.query.filter_by(request_type=req_type).count()
            type_counts[req_type] = count
        
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
    This is the new privacy-compliant approach where current users only provide their own data,
    and new users register independently.
    """
    try:
        current_user = User.query.get(get_jwt_identity())
        
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        transition_request_id = data.get('transition_request_id')
        registration_id = data.get('registration_id')
        new_user_data = data.get('new_user_data')
        
        if not all([transition_request_id, registration_id, new_user_data]):
            return jsonify({'error': 'Missing required data'}), 400
        
        # Get the transition request
        transition_request = UserTransitionRequest.query.get(transition_request_id)
        if not transition_request:
            return jsonify({'error': 'Transition request not found'}), 404
        
        # Get the pending registration
        pending_registration = User.query.filter_by(id=registration_id, status='pending').first()
        if not pending_registration:
            return jsonify({'error': 'Pending registration not found'}), 404
        
        # Verify ERF numbers match
        pending_erf = None
        if pending_registration.resident:
            pending_erf = pending_registration.resident.erf_number
        elif pending_registration.owner:
            pending_erf = pending_registration.owner.erf_number
        
        if transition_request.erf_number != pending_erf:
            return jsonify({'error': f'ERF numbers do not match: transition request has {transition_request.erf_number}, registration has {pending_erf}'}), 400
        
        # Get current user from transition request
        current_user_leaving = User.query.get(transition_request.user_id)
        if not current_user_leaving:
            return jsonify({'error': 'Current user not found'}), 404
        
        # Process the transition using the new approach
        print(f"🔄 Starting linked migration process:")
        print(f"   Transition Request ID: {transition_request_id}")
        print(f"   Registration ID: {registration_id}")
        print(f"   New User Data: {new_user_data}")
        print(f"   Pending User: {pending_registration.email}")
        print(f"   Pending User Status: {pending_registration.status}")
        print(f"   Has Resident Record: {pending_registration.resident is not None}")
        print(f"   Has Owner Record: {pending_registration.owner is not None}")
        
        result = perform_linked_migration(transition_request, current_user_leaving, pending_registration, new_user_data)
        
        if result['success']:
            # Update transition request status
            transition_request.status = 'completed'
            transition_request.migration_completed = True
            transition_request.migration_date = datetime.utcnow()
            transition_request.new_user_id = pending_registration.id
            
            # Note: User status is set in perform_linked_migration function
            print(f"✅ Migration completed for user: {pending_registration.email}")
            
            # Add admin update note
            update = TransitionRequestUpdate(
                transition_request_id=transition_request.id,
                user_id=current_user.id,
                update_text=f"Transition completed by linking with registration {registration_id}. {result['message']}",
                update_type='admin_note',
                old_status='in_progress',
                new_status='completed'
            )
            db.session.add(update)
            
            db.session.commit()
            print(f"✅ Database committed successfully")
            
            return jsonify({
                'message': 'Transition processed successfully',
                'transition_id': transition_request.id,
                'new_user_id': pending_registration.id,
                'migration_type': result.get('migration_type', 'linked_replacement')
            }), 200
        else:
            return jsonify({'error': result['error']}), 500
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error linking and processing transition: {str(e)}")
        return jsonify({'error': f'Failed to process transition: {str(e)}'}), 500


def perform_linked_migration(transition_request, old_user, new_user, new_user_data):
    """
    Comprehensive migration approach that handles ALL transition combinations.
    Supports both complete replacements and partial replacements.
    """
    try:
        print(f"🔗 LINKED MIGRATION: {old_user.email} → {new_user.email}")
        print(f"   ERF: {transition_request.erf_number}")
        print(f"   Expected new type: {transition_request.new_occupant_type}")
        
        # Initialize common variables
        erf_number = transition_request.erf_number
        migration_date = datetime.utcnow()
        migration_reason = f'Linked transition {transition_request.id} with {new_user.email}'
        
        # Determine old user's current role combination
        old_is_resident = old_user.resident and old_user.resident.status == 'active'
        old_is_owner = old_user.owner and old_user.owner.status == 'active'
        
        if old_is_resident and old_is_owner:
            old_role = 'owner_resident'
        elif old_is_owner:
            old_role = 'owner'
        elif old_is_resident:
            old_role = 'resident'
        else:
            old_role = 'unknown'
        
        # Determine new user's intended role from transition request new_occupant_type
        intended_type = transition_request.new_occupant_type
        
        # Map new_occupant_type to role flags
        if intended_type == 'resident':
            new_is_resident = True
            new_is_owner = False
        elif intended_type == 'owner':
            new_is_resident = False
            new_is_owner = True
        elif intended_type == 'owner_resident':
            new_is_resident = True
            new_is_owner = True
        elif intended_type == 'terminated':
            # Special case: current user is leaving estate entirely - no new user needed
            new_is_resident = False
            new_is_owner = False
        else:
            # Fallback to registration data
            new_is_resident = new_user_data.get('is_resident', False)
            new_is_owner = new_user_data.get('is_owner', False)
        
        if new_is_resident and new_is_owner:
            new_role = 'owner_resident'
        elif new_is_owner:
            new_role = 'owner'
        elif new_is_resident:
            new_role = 'resident'
        elif intended_type == 'terminated':
            new_role = 'terminated'  # Special case for leaving estate
        else:
            new_role = 'resident'  # Default
        
        print(f"   🔄 Transition: {old_role} → {new_role} (intended: {intended_type})")
        
        # Special case: If terminated, this is a pure deactivation (no new user)
        if intended_type == 'terminated':
            print(f"   🚪 TERMINATION: Old user exits estate completely")
            
            # Update migration reason for termination
            migration_reason = f'User terminated/exited estate via transition {transition_request.id}'
            
            # Step 1: Deactivate old user completely
            old_user.status = 'inactive' 
            old_user.password_hash = 'DISABLED'
            print(f"   ❌ Deactivated old user: {old_user.email}")
            
            # Step 2: Mark old user's records as deleted_profile
            if old_user.resident:
                old_user.resident.status = 'deleted_profile'
                old_user.resident.migration_date = migration_date
                old_user.resident.migration_reason = migration_reason
                print(f"   📝 Marked old resident record as deleted_profile")
            
            if old_user.owner:
                old_user.owner.status = 'deleted_profile'
                old_user.owner.migration_date = migration_date
                old_user.owner.migration_reason = migration_reason
                print(f"   📝 Marked old owner record as deleted_profile")
            
            # Step 3: Deactivate old vehicles
            old_vehicles = []
            if old_user.resident:
                old_vehicles.extend(Vehicle.query.filter_by(resident_id=old_user.resident.id).all())
            if old_user.owner:
                old_vehicles.extend(Vehicle.query.filter_by(owner_id=old_user.owner.id).all())
            
            for vehicle in old_vehicles:
                vehicle.status = 'inactive'
                vehicle.migration_date = migration_date
                vehicle.migration_reason = migration_reason
                print(f"   🚗 Deactivated vehicle: {vehicle.registration_number}")
            
            # Step 4: Mark transition as completed (no new user)
            transition_request.migration_completed = True
            transition_request.migration_date = migration_date
            transition_request.new_user_id = None  # No new user for termination
            transition_request.status = 'completed'
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Successfully terminated user access for ERF {erf_number}. User exited estate.',
                'migration_type': 'termination',
                'old_user_id': old_user.id,
                'old_user_status': 'inactive',
                'new_user_id': None,
                'vehicles_transferred': 0,
                'vehicles_deactivated': len(old_vehicles)
            }
        
        # Determine transition type for normal transitions (with new user)
        is_partial_replacement = False
        old_keeps_owner = False
        old_keeps_resident = False
        
        if old_role == 'owner_resident':
            if new_role == 'resident':
                # Owner-resident rents out but keeps ownership
                is_partial_replacement = True
                old_keeps_owner = True
                print(f"   📋 PARTIAL REPLACEMENT: Old user keeps owner role")
            elif new_role == 'owner':
                # Owner-resident sells ownership but stays as tenant
                is_partial_replacement = True
                old_keeps_resident = True
                print(f"   📋 PARTIAL REPLACEMENT: Old user keeps resident role")
            else:
                # Complete replacement
                print(f"   📋 COMPLETE REPLACEMENT: Old user loses all roles")
        else:
            # All other scenarios are complete replacements
            print(f"   📋 COMPLETE REPLACEMENT: Old user loses all roles")
        
        # Execute migration based on type
        if is_partial_replacement:
            # PARTIAL REPLACEMENT: Old user keeps active but loses some roles
            print(f"   🔄 Executing partial replacement...")
            
            # Old user stays active
            print(f"   ✅ Keeping old user active: {old_user.email}")
            
            # Handle old user's records based on what they keep
            if old_keeps_owner:
                # Old user keeps owner role, loses resident role
                old_user.role = 'owner'
                if old_user.resident:
                    old_user.resident.status = 'deleted_profile'
                    old_user.resident.migration_date = migration_date
                    old_user.resident.migration_reason = migration_reason
                    print(f"   📝 Marked old resident record as deleted_profile")
                if old_user.owner:
                    print(f"   ✅ Keeping old owner record active")
                    
            elif old_keeps_resident:
                # Old user keeps resident role, loses owner role
                old_user.role = 'resident'
                if old_user.owner:
                    old_user.owner.status = 'deleted_profile'
                    old_user.owner.migration_date = migration_date
                    old_user.owner.migration_reason = migration_reason
                    print(f"   📝 Marked old owner record as deleted_profile")
                if old_user.resident:
                    print(f"   ✅ Keeping old resident record active")
            
            # Vehicles stay with old user (don't transfer)
            print(f"   🚗 Vehicles remain with old user (no transfer)")
            
        else:
            # COMPLETE REPLACEMENT: Old user loses everything
            print(f"   🔄 Executing complete replacement...")
            
            # Step 1: Deactivate old user completely
            old_user.status = 'inactive' 
            old_user.password_hash = 'DISABLED'
            print(f"   ❌ Deactivated old user: {old_user.email}")
            
            # Step 2: Mark old user's records as deleted_profile
            if old_user.resident:
                old_user.resident.status = 'deleted_profile'
                old_user.resident.migration_date = migration_date
                old_user.resident.migration_reason = migration_reason
                print(f"   � Marked old resident record as deleted_profile")
            
            if old_user.owner:
                old_user.owner.status = 'deleted_profile'
                old_user.owner.migration_date = migration_date
                old_user.owner.migration_reason = migration_reason
                print(f"   📝 Marked old owner record as deleted_profile")
            
            # Step 3: Deactivate old vehicles
            old_vehicles = []
            if old_user.resident:
                old_vehicles.extend(Vehicle.query.filter_by(resident_id=old_user.resident.id).all())
            if old_user.owner:
                old_vehicles.extend(Vehicle.query.filter_by(owner_id=old_user.owner.id).all())
            
            for vehicle in old_vehicles:
                vehicle.status = 'inactive'
                vehicle.migration_date = migration_date
                vehicle.migration_reason = migration_reason
                print(f"   🚗 Deactivated vehicle: {vehicle.registration_number}")
        
        # Step 4: Activate new user with appropriate role
        new_user.status = 'active'
        new_user.role = new_role
        print(f"   ✅ Activated new user as {new_role}: {new_user.email}")
        
        # Step 5: Activate new user's existing records based on their role
        if new_is_resident and new_user.resident:
            new_user.resident.status = 'active'
            new_user.resident.erf_number = erf_number
            new_user.resident.intercom_code = 'ADMIN_SET_REQUIRED'
            print(f"   🏠 Activated existing resident record for ERF {erf_number}")
        elif new_is_resident and not new_user.resident:
            # Fallback: create resident record if missing
            new_resident = Resident(
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
            )
            db.session.add(new_resident)
            print(f"   🏠 Created missing resident record for ERF {erf_number}")
        
        if new_is_owner and new_user.owner:
            new_user.owner.status = 'active'
            new_user.owner.erf_number = erf_number
            new_user.owner.intercom_code = 'ADMIN_SET_REQUIRED'
            print(f"   🏠 Activated existing owner record for ERF {erf_number}")
        elif new_is_owner and not new_user.owner:
            # Fallback: create owner record if missing
            new_owner = Owner(
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
                full_postal_address=f'1 Main Street, Suburb, City, 0000',
                status='active'
            )
            db.session.add(new_owner)
            print(f"   🏠 Created missing owner record for ERF {erf_number}")
        
        # Step 6: Record migration completion
        transition_request.migration_completed = True
        transition_request.migration_date = migration_date
        transition_request.new_user_id = new_user.id
        transition_request.status = 'completed'
        
        db.session.commit()
        
        # Create result summary
        vehicles_affected = 0 if is_partial_replacement else len(old_vehicles) if 'old_vehicles' in locals() else 0
        
        return {
            'success': True,
            'message': f'Successfully migrated ERF {erf_number}: {old_role} → {new_role}',
            'migration_type': 'partial_replacement' if is_partial_replacement else 'complete_replacement',
            'old_user_id': old_user.id,
            'old_user_status': 'active' if is_partial_replacement else 'inactive',
            'new_user_id': new_user.id,
            'vehicles_transferred': 0,  # No vehicles transferred (business rule)
            'vehicles_deactivated': vehicles_affected
        }
        
    except Exception as e:
        db.session.rollback()
        print(f"   ❌ Linked migration failed: {str(e)}")
        return {'success': False, 'error': f'Linked migration failed: {str(e)}'}

@transition_bp.route('/admin/request/<request_id>/mark-migration-completed', methods=['PUT'])
@jwt_required()
def mark_transition_migration_completed(request_id):
    """Mark a transition request as migration completed (admin only)"""
    try:
        current_user = User.query.get(get_jwt_identity())
        
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        transition_request = UserTransitionRequest.query.get_or_404(request_id)
        
        # Mark as migration completed
        transition_request.migration_completed = True
        transition_request.migration_date = datetime.utcnow()
        transition_request.updated_at = datetime.utcnow()
        
        # Create update record
        update = TransitionRequestUpdate(
            transition_request_id=request_id,
            user_id=current_user.id,
            update_text="Migration manually marked as completed after successful transition linking",
            update_type='admin_note'
        )
        
        db.session.add(update)
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
    Handle user termination/exit from the estate.
    This deactivates the user and removes them from the gate register.
    """
    try:
        # Get the user being terminated
        user = User.query.get(transition_request.user_id)
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        erf_number = transition_request.erf_number
        
        # Deactivate the user
        user.status = 'inactive'
        
        # Deactivate resident record if exists
        if user.resident:
            user.resident.status = 'inactive'
            user.resident.migration_date = datetime.utcnow()
            user.resident.migration_reason = f'User terminated from ERF {erf_number}'
        
        # Deactivate owner record if exists  
        if user.owner:
            user.owner.status = 'inactive'
            user.owner.migration_date = datetime.utcnow()
            user.owner.migration_reason = f'User terminated from ERF {erf_number}'
        
        # Remove from gate register by deactivating user access
        # The gate register is generated from active users, so deactivating 
        # the user will automatically remove them from the gate register
        
        # Deactivate user vehicles
        vehicles = []
        if user.resident:
            vehicles.extend(Vehicle.query.filter_by(resident_id=user.resident.id).all())
        if user.owner:
            vehicles.extend(Vehicle.query.filter_by(owner_id=user.owner.id).all())
            
        for vehicle in vehicles:
            vehicle.status = 'terminated'
            vehicle.migration_date = datetime.utcnow()
            vehicle.migration_reason = f'User terminated from ERF {erf_number}'
        
        # Log the termination
        user_name = "Unknown User"
        if user.resident:
            user_name = f"{user.resident.first_name} {user.resident.last_name}"
        elif user.owner:
            user_name = f"{user.owner.first_name} {user.owner.last_name}"
        elif hasattr(user, 'full_name') and user.full_name:
            user_name = user.full_name
        
        log_user_change(
            user.id, 
            user_name,
            erf_number,
            'transition_termination',
            'user_status',
            'active',
            'terminated'
        )
        
        # Mark transition request as migration completed
        transition_request.migration_completed = True
        transition_request.migration_date = datetime.utcnow()
        
        # Add update record
        update = TransitionRequestUpdate(
            transition_request_id=transition_request.id,
            user_id=transition_request.user_id,
            update_text=f"User terminated and removed from ERF {erf_number}. All access revoked.",
            update_type='termination'
        )
        
        db.session.add(update)
        db.session.commit()
        
        return {
            'success': True, 
            'message': f'User successfully terminated and removed from ERF {erf_number}',
            'user_id': user.id,
            'erf_number': erf_number
        }
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error handling user termination: {str(e)}")
        return {'success': False, 'error': f'Termination failed: {str(e)}'}


def find_pending_user_for_erf(erf_number):
    """
    Find a pending user registration for the specified ERF number.
    This is used to check if there's a new occupant waiting to be linked.
    """
    try:
        # Look for pending users who have registered for this ERF
        # Use simpler queries to avoid join issues
        
        # Check pending residents
        residents = Resident.query.filter_by(erf_number=erf_number).all()
        for resident in residents:
            if resident.user and resident.user.status == 'pending':
                return resident.user
        
        # Check pending owners
        owners = Owner.query.filter_by(erf_number=erf_number).all()
        for owner in owners:
            if owner.user and owner.user.status == 'pending':
                return owner.user
        
        return None
        
    except Exception as e:
        current_app.logger.error(f"Error finding pending user for ERF {erf_number}: {str(e)}")
        return None


def handle_transition_linking(transition_request, new_user):
    """
    Handle the linking of a transition request with a new user.
    This activates the new user and deactivates the old user.
    
    ⚠️ IMPORTANT: This function should only be called from the dedicated
    Transition Linking interface, not from the status update endpoint.
    """
    try:
        old_user = User.query.get(transition_request.user_id)
        if not old_user:
            return {'success': False, 'error': 'Old user not found'}
        
        erf_number = transition_request.erf_number
        
        # Step 1: Activate the new user (this is the key step - new user goes from pending to active)
        new_user.status = 'active'
        
        # Step 2: Deactivate the old user (remove from gate register)
        old_user.status = 'inactive'
        
        # Step 3: Update old user's records as migrated (not deleted)
        migration_reason = f'Transitioned to new occupant {new_user.email} via transition {transition_request.id}'
        
        if old_user.resident:
            old_user.resident.status = 'migrated'
            old_user.resident.migration_date = datetime.utcnow()
            old_user.resident.migration_reason = migration_reason
        
        if old_user.owner:
            old_user.owner.status = 'migrated'
            old_user.owner.migration_date = datetime.utcnow()
            old_user.owner.migration_reason = migration_reason
        
        # Step 4: Transfer or deactivate vehicles (remove from old user's gate access)
        vehicles = []
        if old_user.resident:
            vehicles.extend(Vehicle.query.filter_by(resident_id=old_user.resident.id).all())
        if old_user.owner:
            vehicles.extend(Vehicle.query.filter_by(owner_id=old_user.owner.id).all())
            
        for vehicle in vehicles:
            vehicle.status = 'transferred'
            vehicle.migration_date = datetime.utcnow()
            vehicle.migration_reason = f'Owner transitioned from {old_user.email} to {new_user.email}'
        
        # Step 5: Log the transition
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
        
        log_user_change(
            new_user.id, 
            new_user_name,
            erf_number,
            'transition_linking',
            'user_status',
            'pending',
            'active'
        )
        
        log_user_change(
            old_user.id, 
            old_user_name,
            erf_number,
            'transition_linking',
            'user_status',
            'active',
            'inactive'
        )
        
        # Step 6: Mark the transition request as migration completed
        transition_request.migration_completed = True
        transition_request.migration_date = datetime.utcnow()
        
        # Step 7: Add update record
        update = TransitionRequestUpdate(
            transition_request_id=transition_request.id,
            user_id=transition_request.user_id,
            update_text=f"Transition linking completed: {old_user_name} replaced by {new_user_name} for ERF {erf_number}. Old user removed from gate register, new user activated.",
            update_type='linking_completed'
        )
        
        db.session.add(update)
        db.session.commit()
        
        return {
            'success': True, 
            'message': f'Transition linking completed: {old_user_name} → {new_user_name} for ERF {erf_number}. New user activated and added to gate register.',
            'old_user_id': old_user.id,
            'new_user_id': new_user.id,
            'erf_number': erf_number
        }
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error handling transition linking: {str(e)}")
        return {'success': False, 'error': f'Linking failed: {str(e)}'}
