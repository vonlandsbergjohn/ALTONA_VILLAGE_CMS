"""
User Transition Request API Routes
Handles property move-out, sales, and tenant changes
Following the same pattern as the complaint system
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.user import db, User, Resident, Owner, UserTransitionRequest, TransitionRequestUpdate, TransitionVehicle, Vehicle
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
        
        # Step 6: Handle vehicle transfers if requested
        if transition_request.vehicle_registration_transfer:
            transition_vehicles = TransitionVehicle.query.filter_by(
                transition_request_id=transition_request.id
            ).all()
            
            for trans_vehicle in transition_vehicles:
                new_vehicle = Vehicle(
                    resident_id=new_resident.id if new_resident else None,
                    owner_id=new_owner.id if new_owner and not new_resident else None,
                    registration_number=trans_vehicle.license_plate,
                    make=trans_vehicle.vehicle_make,
                    model=trans_vehicle.vehicle_model,
                    color=trans_vehicle.color or 'Unknown',
                    status='active'
                )
                db.session.add(new_vehicle)
                print(f"   🚗 Transferred vehicle: {trans_vehicle.license_plate} ({trans_vehicle.vehicle_make} {trans_vehicle.vehicle_model})")
        
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
        required_fields = ['erf_number', 'request_type', 'current_role']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate request type
        valid_request_types = ['owner_sale', 'tenant_moveout', 'owner_moving', 'other']
        if data['request_type'] not in valid_request_types:
            return jsonify({'error': 'Invalid request type'}), 400
        
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
            
            # Check if this is a privacy-compliant transition request (no new occupant data)
            is_privacy_compliant = (
                not transition_request.new_occupant_first_name or 
                transition_request.new_occupant_first_name.strip() == '' or
                not transition_request.new_occupant_last_name or 
                transition_request.new_occupant_last_name.strip() == '' or
                not transition_request.expected_new_occupant_type or
                transition_request.expected_new_occupant_type in ['', 'unknown', None]
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
                    not transition_request.expected_new_occupant_type or
                    transition_request.expected_new_occupant_type in ['', 'unknown', None]
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
            
            # Approve the pending registration (this should already be done in perform_linked_migration but double-check)
            pending_registration.status = 'approved'
            print(f"✅ Set pending registration status to approved: {pending_registration.email}")
            
            # Add admin update note
            update = TransitionRequestUpdate(
                transition_request_id=transition_request.id,
                admin_id=current_user.id,
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
    New migration approach that works with the privacy-compliant workflow.
    Links a transition request with a separately registered new user.
    """
    try:
        print(f"🔗 LINKED MIGRATION: {old_user.email} → {new_user.email}")
        print(f"   ERF: {transition_request.erf_number}")
        print(f"   Expected type: {transition_request.expected_new_occupant_type}")
        
        # Step 1: Deactivate old user completely
        old_user.status = 'inactive' 
        old_user.password_hash = 'DISABLED'
        print(f"   ❌ Deactivated old user: {old_user.email}")
        
        # Step 2: Mark old user's records as deleted_profile for audit trail
        erf_number = transition_request.erf_number
        migration_reason = f'Replaced by {new_user.email} via linked transition {transition_request.id}'
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
        
        # Step 4: Update new user's role and activate existing records
        # The new user already has resident/owner records from registration, just need to approve and activate
        new_user.status = 'approved'  # Approve the registration
        
        # Determine role from registration data
        is_owner = new_user_data.get('is_owner', False)
        is_resident = new_user_data.get('is_resident', False)
        
        if is_owner and is_resident:
            new_user.role = 'owner_resident'
        elif is_owner:
            new_user.role = 'owner'
        elif is_resident:
            new_user.role = 'resident'
        else:
            new_user.role = 'resident'  # Default
        
        # Step 5: Activate existing resident record if user is a resident
        if is_resident and new_user.resident:
            new_user.resident.status = 'active'
            new_user.resident.erf_number = erf_number  # Ensure ERF number is correct
            new_user.resident.intercom_code = 'ADMIN_SET_REQUIRED'  # Will be set by admin
            print(f"   🏠 Activated existing resident record for ERF {erf_number}")
        elif is_resident and not new_user.resident:
            # Fallback: create resident record if somehow missing
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
            
            # Parse address if provided
            address = new_user_data.get('address', '')
            if ' ' in address:
                parts = address.split(' ', 1)
                new_resident.street_number = parts[0]
                new_resident.street_name = parts[1]
            
            db.session.add(new_resident)
            print(f"   🏠 Created missing resident record for ERF {erf_number}")
        
        # Step 6: Activate existing owner record if user is an owner
        if is_owner and new_user.owner:
            new_user.owner.status = 'active'
            new_user.owner.erf_number = erf_number  # Ensure ERF number is correct
            new_user.owner.intercom_code = 'ADMIN_SET_REQUIRED'  # Will be set by admin
            print(f"   🏠 Activated existing owner record for ERF {erf_number}")
        elif is_owner and not new_user.owner:
            # Fallback: create owner record if somehow missing
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
                title_deed_number='T000000',  # Admin should set this
                postal_street_number='1',
                postal_street_name='Main Street',
                postal_suburb='Suburb',
                postal_city='City',
                postal_code='0000',
                postal_province='Province',
                full_postal_address=f'1 Main Street, Suburb, City, 0000',
                status='active'
            )
            
            # Parse address if provided
            address = new_user_data.get('address', '')
            if ' ' in address:
                parts = address.split(' ', 1)
                new_owner.street_number = parts[0]
                new_owner.street_name = parts[1]
            
            db.session.add(new_owner)
            print(f"   🏠 Created missing owner record for ERF {erf_number}")
        
        # Step 7: Handle vehicle transfers if requested
        if transition_request.vehicle_registration_transfer and old_vehicles:
            for old_vehicle in old_vehicles:
                if old_vehicle.status == 'inactive':  # Only transfer the ones we just deactivated
                    # Create new vehicle record for new user
                    new_vehicle = Vehicle(
                        registration_number=old_vehicle.registration_number,
                        make=old_vehicle.make,
                        model=old_vehicle.model,
                        color=old_vehicle.color,
                        status='active',
                        migration_date=migration_date,
                        migration_reason=f'Transferred from {old_user.email} via transition {transition_request.id}'
                    )
                    
                    # Link to appropriate record
                    if new_user.resident:
                        new_vehicle.resident_id = new_user.resident.id
                    elif new_user.owner:
                        new_vehicle.owner_id = new_user.owner.id
                    
                    db.session.add(new_vehicle)
                    print(f"   🚗 Transferred vehicle: {old_vehicle.registration_number}")
        
        db.session.commit()
        
        return {
            'success': True,
            'message': f'Successfully migrated ERF {erf_number} from {old_user.email} to {new_user.email}',
            'migration_type': 'linked_replacement',
            'old_user_id': old_user.id,
            'new_user_id': new_user.id,
            'vehicles_transferred': len([v for v in old_vehicles if transition_request.vehicle_registration_transfer])
        }
        
    except Exception as e:
        db.session.rollback()
        print(f"   ❌ Linked migration failed: {str(e)}")
        return {'success': False, 'error': f'Linked migration failed: {str(e)}'}
