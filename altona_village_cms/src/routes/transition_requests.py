"""
User Transition Request API Routes
Handles property move-out, sales, and tenant changes
Following the same pattern as the complaint system
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.user import db, User, Resident, Owner, UserTransitionRequest, TransitionRequestUpdate, TransitionVehicle
from datetime import datetime, date
import uuid

transition_bp = Blueprint('transition', __name__)

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
            if field in data and data[field] is not None:
                setattr(transition_request, field, int(data.get(field)))
        
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
