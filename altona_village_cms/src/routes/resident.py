from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import User, Resident, Owner, Vehicle, Complaint, ComplaintUpdate, db

# Import change tracking function
try:
    from src.routes.admin_notifications import log_user_change
except ImportError:
    # Fallback if admin_notifications module doesn't exist yet
    def log_user_change(*args, **kwargs):
        pass

resident_bp = Blueprint('resident', __name__)

def get_current_user_data():
    """Get current user data (supports both residents and owners)"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return None, None, None
    
    # Return user and their resident/owner data
    resident_data = user.resident if user.is_resident() else None
    owner_data = user.owner if user.is_owner() else None
    
    return user, resident_data, owner_data

def get_current_resident():
    """Get current resident from JWT token (legacy function)"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'resident':
        return None
    return user.resident

@resident_bp.route('/vehicles', methods=['GET'])
@jwt_required()
def get_my_vehicles():
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get all user accounts with the same email (for multi-ERF support)
        all_user_accounts = User.query.filter_by(email=current_user.email).all()
        
        vehicles = []
        seen_vehicle_ids = set()  # Track vehicles to avoid duplicates
        
        # Get vehicles from all user accounts with this email
        for user_account in all_user_accounts:
            # Get vehicles for residents
            if user_account.resident:
                resident_vehicles = Vehicle.query.filter_by(resident_id=user_account.resident.id).all()
                for vehicle in resident_vehicles:
                    if vehicle.id not in seen_vehicle_ids:
                        vehicle_dict = vehicle.to_dict()
                        # Add ERF information
                        vehicle_dict['erf_number'] = user_account.resident.erf_number
                        vehicle_dict['property_address'] = user_account.resident.full_address or 'Address not available'
                        vehicle_dict['user_id'] = user_account.id
                        vehicles.append(vehicle_dict)
                        seen_vehicle_ids.add(vehicle.id)
            
            # Get vehicles for owners (including owner-only users)
            if user_account.owner:
                owner_vehicles = Vehicle.query.filter_by(owner_id=user_account.owner.id).all()
                for vehicle in owner_vehicles:
                    if vehicle.id not in seen_vehicle_ids:
                        vehicle_dict = vehicle.to_dict()
                        # Add ERF information
                        vehicle_dict['erf_number'] = user_account.owner.erf_number
                        vehicle_dict['property_address'] = user_account.owner.full_address or 'Address not available'
                        vehicle_dict['user_id'] = user_account.id
                        vehicles.append(vehicle_dict)
                        seen_vehicle_ids.add(vehicle.id)
        
        return jsonify(vehicles), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@resident_bp.route('/vehicles', methods=['POST'])
@jwt_required()
def add_vehicle():
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if not current_user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()
        
        # Check if registration number already exists
        if Vehicle.query.filter_by(registration_number=data['registration_number']).first():
            return jsonify({'error': 'Vehicle with this registration number already exists'}), 400

        # Get all user accounts with the same email (for multi-ERF support)
        all_user_accounts = User.query.filter_by(email=current_user.email).all()
        
        # Determine which ERF/user account this vehicle should be assigned to
        target_user_id = data.get('erf_selection')  # Frontend sends the selected user_id
        
        if target_user_id:
            # Multi-ERF user - validate that the selected user_id belongs to this email
            target_user = next((user for user in all_user_accounts if user.id == target_user_id), None)
            if not target_user:
                return jsonify({'error': 'Invalid ERF selection'}), 400
        else:
            # Single ERF user or no selection - use current user
            target_user = current_user
        
        # Get the resident/owner data for the target user
        target_resident = target_user.resident if target_user.is_resident() else None
        target_owner = target_user.owner if target_user.is_owner() else None
        
        if not target_resident and not target_owner:
            return jsonify({'error': 'Selected ERF has no resident or owner data'}), 400

        # Create vehicle - prefer resident_id if available, otherwise use owner_id
        vehicle = Vehicle(
            resident_id=target_resident.id if target_resident else None,
            owner_id=target_owner.id if (target_owner and not target_resident) else None,
            registration_number=data['registration_number'],
            make=data.get('make'),
            model=data.get('model'),
            color=data.get('color')
        )
        
        db.session.add(vehicle)
        db.session.commit()
        
        # Log vehicle addition for change tracking
        try:
            # Get user display name and ERF number for logging
            if target_resident:
                user_name = f"{target_resident.first_name} {target_resident.last_name}".strip()
                erf_number = target_resident.erf_number or 'Unknown'
            elif target_owner:
                user_name = f"{target_owner.first_name} {target_owner.last_name}".strip()
                erf_number = target_owner.erf_number or 'Unknown'
            else:
                user_name = target_user.email
                erf_number = 'Unknown'
            
            # Log the new vehicle addition
            log_user_change(
                target_user.id, 
                user_name, 
                erf_number, 
                'user_add', 
                'vehicle_registration', 
                'None', 
                data['registration_number']
            )
            
            # Also log other vehicle details if provided
            if data.get('make'):
                log_user_change(target_user.id, user_name, erf_number, 'user_add', 'vehicle_make', 'None', data['make'])
            
            if data.get('model'):
                log_user_change(target_user.id, user_name, erf_number, 'user_add', 'vehicle_model', 'None', data['model'])
            
            if data.get('color'):
                log_user_change(target_user.id, user_name, erf_number, 'user_add', 'vehicle_color', 'None', data['color'])
                
        except Exception as log_error:
            print(f"Error logging user vehicle addition: {log_error}")
        
        return jsonify(vehicle.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@resident_bp.route('/vehicles/<vehicle_id>', methods=['PUT'])
@jwt_required()
def update_vehicle(vehicle_id):
    try:
        user, resident_data, owner_data = get_current_user_data()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Find vehicle belonging to this user (resident or owner)
        vehicle = None
        if resident_data:
            vehicle = Vehicle.query.filter_by(id=vehicle_id, resident_id=resident_data.id).first()
        if not vehicle and owner_data:
            vehicle = Vehicle.query.filter_by(id=vehicle_id, owner_id=owner_data.id).first()
        
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        data = request.get_json()
        
        # Check if new registration number already exists (excluding current vehicle)
        if 'registration_number' in data:
            existing = Vehicle.query.filter_by(registration_number=data['registration_number']).first()
            if existing and existing.id != vehicle_id:
                return jsonify({'error': 'Vehicle with this registration number already exists'}), 400
            
            # Track vehicle registration changes for camera system
            if vehicle.registration_number != data['registration_number']:
                # Get user details for logging
                user_name = f"{getattr(user.resident, 'first_name', '') or getattr(user.owner, 'first_name', '')} {getattr(user.resident, 'last_name', '') or getattr(user.owner, 'last_name', '')}".strip()
                erf_number = getattr(user.resident, 'erf_number', '') or getattr(user.owner, 'erf_number', '') or 'Unknown'
                
                try:
                    log_user_change(
                        user_id=user.id,
                        user_name=user_name,
                        erf_number=erf_number,
                        change_type="vehicle_update",
                        field_name="vehicle_registration",
                        old_value=vehicle.registration_number or '',
                        new_value=data['registration_number']
                    )
                except Exception as e:
                    print(f"Failed to log vehicle registration change: {str(e)}")
            
            vehicle.registration_number = data['registration_number']
        
        vehicle.make = data.get('make', vehicle.make)
        vehicle.model = data.get('model', vehicle.model)
        vehicle.color = data.get('color', vehicle.color)
        
        db.session.commit()
        
        return jsonify(vehicle.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@resident_bp.route('/vehicles/<vehicle_id>', methods=['DELETE'])
@jwt_required()
def delete_vehicle(vehicle_id):
    try:
        user, resident_data, owner_data = get_current_user_data()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Find vehicle belonging to this user (resident or owner)
        vehicle = None
        if resident_data:
            vehicle = Vehicle.query.filter_by(id=vehicle_id, resident_id=resident_data.id).first()
        if not vehicle and owner_data:
            vehicle = Vehicle.query.filter_by(id=vehicle_id, owner_id=owner_data.id).first()
        
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        db.session.delete(vehicle)
        db.session.commit()
        
        return jsonify({'message': 'Vehicle deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@resident_bp.route('/complaints', methods=['GET'])
@jwt_required()
def get_my_complaints():
    try:
        resident = get_current_resident()
        if not resident:
            return jsonify({'error': 'Resident not found'}), 404
        
        complaints = []
        for complaint in resident.complaints:
            complaint_data = complaint.to_dict()
            
            # Add updates with user information
            if complaint.updates:
                updates_with_user = []
                for update in complaint.updates:
                    update_data = update.to_dict()
                    # Get the user who made the update (admin)
                    update_user = User.query.get(update.user_id)
                    if update_user:
                        update_data['admin_name'] = update_user.get_full_name()
                        update_data['admin_role'] = update_user.role
                    updates_with_user.append(update_data)
                complaint_data['updates'] = updates_with_user
            
            complaints.append(complaint_data)
        
        return jsonify(complaints), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@resident_bp.route('/complaints', methods=['POST'])
@jwt_required()
def submit_complaint():
    try:
        resident = get_current_resident()
        if not resident:
            return jsonify({'error': 'Resident not found'}), 404
        
        data = request.get_json()
        
        complaint = Complaint(
            resident_id=resident.id,
            subject=data['subject'],
            description=data['description'],
            priority=data.get('priority', 'medium')
        )
        
        db.session.add(complaint)
        db.session.commit()
        
        return jsonify(complaint.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@resident_bp.route('/complaints/<complaint_id>', methods=['GET'])
@jwt_required()
def get_complaint(complaint_id):
    try:
        resident = get_current_resident()
        if not resident:
            return jsonify({'error': 'Resident not found'}), 404
        
        complaint = Complaint.query.filter_by(id=complaint_id, resident_id=resident.id).first()
        if not complaint:
            return jsonify({'error': 'Complaint not found'}), 404
        
        complaint_data = complaint.to_dict()
        
        # Add updates with user information
        if complaint.updates:
            updates_with_user = []
            for update in complaint.updates:
                update_data = update.to_dict()
                # Get the user who made the update (admin)
                update_user = User.query.get(update.user_id)
                if update_user:
                    update_data['admin_name'] = update_user.get_full_name()
                    update_data['admin_role'] = update_user.role
                updates_with_user.append(update_data)
            complaint_data['updates'] = updates_with_user
        
        return jsonify(complaint_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@resident_bp.route('/properties', methods=['GET'])
@jwt_required()
def get_my_properties():
    try:
        resident = get_current_resident()
        if not resident:
            return jsonify({'error': 'Resident not found'}), 404
        
        properties = []
        for prop in resident.properties:
            prop_data = prop.to_dict()
            
            # Add meter information
            if prop.meters:
                prop_data['meters'] = [meter.to_dict() for meter in prop.meters]
            
            properties.append(prop_data)
        
        return jsonify(properties), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

