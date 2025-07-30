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
    Migrate user from transition request to production database when status becomes 'completed'
    This handles:
    1. Moving old user to inactive status
    2. Creating new user records in production database
    3. Updating Gate Register with new user data
    4. Preserving audit trail
    """
    try:
        # Only process if we have new occupant information
        if (not transition_request.new_occupant_type or 
            transition_request.new_occupant_type == 'unknown' or
            not transition_request.new_occupant_first_name or
            not transition_request.new_occupant_last_name):
            return {'success': True, 'message': 'No new occupant data to migrate'}
        
        # Find the current user (old occupant)
        current_user = User.query.get(transition_request.user_id)
        if not current_user:
            return {'success': False, 'error': 'Current user not found'}
        
        # Step 1: Mark old user as inactive
        current_user.status = 'inactive'
        
        # Step 2: Create new user account
        new_user_email = transition_request.new_occupant_email
        if not new_user_email:
            # Generate a temporary email if none provided
            new_user_email = f"temp_{transition_request.new_occupant_first_name.lower()}_{transition_request.new_occupant_last_name.lower()}@altona-village.temp"
        
        # Check if user with this email already exists
        existing_user = User.query.filter_by(email=new_user_email).first()
        if existing_user:
            return {'success': False, 'error': f'User with email {new_user_email} already exists'}
        
        # Create new user
        new_user = User(
            email=new_user_email,
            password_hash=current_user.password_hash,  # Temporary - user will need to reset
            full_name=f"{transition_request.new_occupant_first_name} {transition_request.new_occupant_last_name}",
            role='resident',  # Default role, will be adjusted based on occupant type
            status='active'
        )
        db.session.add(new_user)
        db.session.flush()  # Get new_user.id
        
        # Step 3: Create appropriate records based on new occupant type
        if transition_request.new_occupant_type == 'new_tenant':
            # Create resident record
            resident = Resident(
                user_id=new_user.id,
                first_name=transition_request.new_occupant_first_name,
                last_name=transition_request.new_occupant_last_name,
                phone_number=transition_request.new_occupant_phone or '',
                emergency_contact_name=transition_request.new_occupant_emergency_contact_name or '',
                emergency_contact_number=transition_request.new_occupant_emergency_contact_number or '',
                id_number=transition_request.new_occupant_id_number or '',
                erf_number=transition_request.erf_number,
                street_number=transition_request.new_occupant_street_number or '',
                street_name=transition_request.new_occupant_street_name or '',
                full_address=transition_request.new_occupant_full_address or '',
                intercom_code=transition_request.new_occupant_intercom_code or '',
                moving_in_date=transition_request.new_occupant_moving_in_date
            )
            db.session.add(resident)
            
        elif transition_request.new_occupant_type == 'new_owner':
            # Create owner record
            owner = Owner(
                user_id=new_user.id,
                first_name=transition_request.new_occupant_first_name,
                last_name=transition_request.new_occupant_last_name,
                phone_number=transition_request.new_occupant_phone or '',
                emergency_contact_name=transition_request.new_occupant_emergency_contact_name or '',
                emergency_contact_number=transition_request.new_occupant_emergency_contact_number or '',
                id_number=transition_request.new_occupant_id_number or '',
                erf_number=transition_request.erf_number,
                street_number=transition_request.new_occupant_street_number or '',
                street_name=transition_request.new_occupant_street_name or '',
                full_address=transition_request.new_occupant_full_address or '',
                intercom_code=transition_request.new_occupant_intercom_code or '',
                title_deed_number=transition_request.new_occupant_title_deed_number or '',
                acquisition_date=transition_request.new_occupant_acquisition_date,
                postal_street_number=transition_request.new_occupant_postal_street_number or '',
                postal_street_name=transition_request.new_occupant_postal_street_name or '',
                postal_suburb=transition_request.new_occupant_postal_suburb or '',
                postal_city=transition_request.new_occupant_postal_city or '',
                postal_code=transition_request.new_occupant_postal_code or '',
                postal_province=transition_request.new_occupant_postal_province or '',
                full_postal_address=transition_request.new_occupant_full_postal_address or ''
            )
            db.session.add(owner)
            
        elif transition_request.new_occupant_type == 'owner_resident':
            # Create both resident and owner records
            resident = Resident(
                user_id=new_user.id,
                first_name=transition_request.new_occupant_first_name,
                last_name=transition_request.new_occupant_last_name,
                phone_number=transition_request.new_occupant_phone or '',
                emergency_contact_name=transition_request.new_occupant_emergency_contact_name or '',
                emergency_contact_number=transition_request.new_occupant_emergency_contact_number or '',
                id_number=transition_request.new_occupant_id_number or '',
                erf_number=transition_request.erf_number,
                street_number=transition_request.new_occupant_street_number or '',
                street_name=transition_request.new_occupant_street_name or '',
                full_address=transition_request.new_occupant_full_address or '',
                intercom_code=transition_request.new_occupant_intercom_code or '',
                moving_in_date=transition_request.new_occupant_moving_in_date
            )
            db.session.add(resident)
            
            owner = Owner(
                user_id=new_user.id,
                first_name=transition_request.new_occupant_first_name,
                last_name=transition_request.new_occupant_last_name,
                phone_number=transition_request.new_occupant_phone or '',
                emergency_contact_name=transition_request.new_occupant_emergency_contact_name or '',
                emergency_contact_number=transition_request.new_occupant_emergency_contact_number or '',
                id_number=transition_request.new_occupant_id_number or '',
                erf_number=transition_request.erf_number,
                street_number=transition_request.new_occupant_street_number or '',
                street_name=transition_request.new_occupant_street_name or '',
                full_address=transition_request.new_occupant_full_address or '',
                intercom_code=transition_request.new_occupant_intercom_code or '',
                title_deed_number=transition_request.new_occupant_title_deed_number or '',
                acquisition_date=transition_request.new_occupant_acquisition_date,
                postal_street_number=transition_request.new_occupant_postal_street_number or '',
                postal_street_name=transition_request.new_occupant_postal_street_name or '',
                postal_suburb=transition_request.new_occupant_postal_suburb or '',
                postal_city=transition_request.new_occupant_postal_city or '',
                postal_code=transition_request.new_occupant_postal_code or '',
                postal_province=transition_request.new_occupant_postal_province or '',
                full_postal_address=transition_request.new_occupant_full_postal_address or ''
            )
            db.session.add(owner)
        
        # Step 4: Migrate vehicles if requested
        if transition_request.vehicle_registration_transfer:
            # Get transition vehicles for this request
            transition_vehicles = TransitionVehicle.query.filter_by(
                transition_request_id=transition_request.id
            ).all()
            
            for trans_vehicle in transition_vehicles:
                # Create new vehicle record for the new user
                new_vehicle = Vehicle(
                    resident_id=resident.id if 'resident' in locals() else None,
                    owner_id=owner.id if 'owner' in locals() and 'resident' not in locals() else None,
                    registration_number=trans_vehicle.license_plate,
                    make=trans_vehicle.vehicle_make,
                    model=trans_vehicle.vehicle_model,
                    color=getattr(trans_vehicle, 'color', None)  # Handle missing color field
                )
                db.session.add(new_vehicle)
        
        # Step 5: Transfer old user vehicles to inactive (don't delete, preserve audit trail)
        if current_user.resident:
            old_vehicles = Vehicle.query.filter_by(resident_id=current_user.resident.id).all()
            for vehicle in old_vehicles:
                vehicle.status = 'inactive'  # Assume we add status field to Vehicle model
        
        if current_user.owner:
            old_vehicles = Vehicle.query.filter_by(owner_id=current_user.owner.id).all()
            for vehicle in old_vehicles:
                vehicle.status = 'inactive'
        
        # Step 6: Record migration in transition request
        transition_request.migration_completed = True
        transition_request.migration_date = datetime.utcnow()
        transition_request.new_user_id = new_user.id
        
        # Commit all changes
        db.session.commit()
        
        return {
            'success': True, 
            'message': f'User migration completed successfully. New user created: {new_user.email}',
            'new_user_id': new_user.id,
            'old_user_id': current_user.id
        }
        
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': f'Migration failed: {str(e)}'}

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
                        license_plate=vehicle_data.get('license_plate')
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
            # Perform user migration from transition data to production database
            migration_result = perform_user_migration(transition_request)
            if not migration_result['success']:
                current_app.logger.error(f"User migration failed: {migration_result['error']}")
                # Don't fail the status update, but log the error
        
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
                # Perform user migration from transition data to production database
                migration_result = perform_user_migration(transition_request)
                if not migration_result['success']:
                    current_app.logger.error(f"User migration failed: {migration_result['error']}")
                    # Don't fail the status update, but log the error
        
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
