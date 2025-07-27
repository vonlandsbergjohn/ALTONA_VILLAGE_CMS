from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import User, Resident, Vehicle, Complaint, ComplaintUpdate, db

resident_bp = Blueprint('resident', __name__)

def get_current_resident():
    """Get current resident from JWT token"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'resident':
        return None
    return user.resident

@resident_bp.route('/vehicles', methods=['GET'])
@jwt_required()
def get_my_vehicles():
    try:
        resident = get_current_resident()
        if not resident:
            return jsonify({'error': 'Resident not found'}), 404
        
        vehicles = [vehicle.to_dict() for vehicle in resident.vehicles]
        return jsonify(vehicles), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@resident_bp.route('/vehicles', methods=['POST'])
@jwt_required()
def add_vehicle():
    try:
        resident = get_current_resident()
        if not resident:
            return jsonify({'error': 'Resident not found'}), 404
        
        data = request.get_json()
        
        # Check if registration number already exists
        if Vehicle.query.filter_by(registration_number=data['registration_number']).first():
            return jsonify({'error': 'Vehicle with this registration number already exists'}), 400
        
        vehicle = Vehicle(
            resident_id=resident.id,
            registration_number=data['registration_number'],
            make=data.get('make'),
            model=data.get('model'),
            color=data.get('color')
        )
        
        db.session.add(vehicle)
        db.session.commit()
        
        return jsonify(vehicle.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@resident_bp.route('/vehicles/<vehicle_id>', methods=['PUT'])
@jwt_required()
def update_vehicle(vehicle_id):
    try:
        resident = get_current_resident()
        if not resident:
            return jsonify({'error': 'Resident not found'}), 404
        
        vehicle = Vehicle.query.filter_by(id=vehicle_id, resident_id=resident.id).first()
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        data = request.get_json()
        
        # Check if new registration number already exists (excluding current vehicle)
        if 'registration_number' in data:
            existing = Vehicle.query.filter_by(registration_number=data['registration_number']).first()
            if existing and existing.id != vehicle_id:
                return jsonify({'error': 'Vehicle with this registration number already exists'}), 400
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
        resident = get_current_resident()
        if not resident:
            return jsonify({'error': 'Resident not found'}), 404
        
        vehicle = Vehicle.query.filter_by(id=vehicle_id, resident_id=resident.id).first()
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

