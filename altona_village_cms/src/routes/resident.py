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
        user, resident_data, owner_data = get_current_user_data()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        vehicles = []
        
        # Get vehicles for residents
        if resident_data:
            resident_vehicles = Vehicle.query.filter_by(resident_id=resident_data.id).all()
            vehicles.extend([vehicle.to_dict() for vehicle in resident_vehicles])
        
        # Get vehicles for owners (including owner-only users)
        if owner_data:
            owner_vehicles = Vehicle.query.filter_by(owner_id=owner_data.id).all()
            vehicles.extend([vehicle.to_dict() for vehicle in owner_vehicles])
        
        return jsonify(vehicles), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@resident_bp.route('/vehicles', methods=['POST'])
@jwt_required()
def add_vehicle():
    try:
        user, resident_data, owner_data = get_current_user_data()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Both residents and owners can register vehicles
        if not resident_data and not owner_data:
            return jsonify({'error': 'Only residents and owners can register vehicles'}), 403
        
        data = request.get_json()
        
        # Check if registration number already exists
        if Vehicle.query.filter_by(registration_number=data['registration_number']).first():
            return jsonify({'error': 'Vehicle with this registration number already exists'}), 400
        
        # Create vehicle - prefer resident_id if available, otherwise use owner_id
        vehicle = Vehicle(
            resident_id=resident_data.id if resident_data else None,
            owner_id=owner_data.id if (owner_data and not resident_data) else None,
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
            if resident_data:
                user_name = f"{resident_data.first_name} {resident_data.last_name}".strip()
                erf_number = resident_data.erf_number or 'Unknown'
            elif owner_data:
                user_name = f"{owner_data.first_name} {owner_data.last_name}".strip()
                erf_number = owner_data.erf_number or 'Unknown'
            else:
                user_name = user.email
                erf_number = 'Unknown'
            
            # Log the new vehicle addition
            log_user_change(
                user.id, 
                user_name, 
                erf_number, 
                'user_add', 
                'vehicle_registration', 
                'None', 
                data['registration_number']
            )
            
            # Also log other vehicle details if provided
            if data.get('make'):
                log_user_change(user.id, user_name, erf_number, 'user_add', 'vehicle_make', 'None', data['make'])
            
            if data.get('model'):
                log_user_change(user.id, user_name, erf_number, 'user_add', 'vehicle_model', 'None', data['model'])
            
            if data.get('color'):
                log_user_change(user.id, user_name, erf_number, 'user_add', 'vehicle_color', 'None', data['color'])
                
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

