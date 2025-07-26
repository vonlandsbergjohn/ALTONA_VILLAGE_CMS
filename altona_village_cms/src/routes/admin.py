from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import User, Resident, Property, Vehicle, Builder, Meter, Complaint, ComplaintUpdate, db
from src.utils.email_service import send_approval_email, send_rejection_email
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

def admin_required():
    """Decorator to check if user is admin"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    return None

@admin_bp.route('/pending-registrations', methods=['GET'])
@jwt_required()
def get_pending_registrations():
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        pending_users = User.query.filter_by(status='pending').all()
        result = []
        
        for user in pending_users:
            user_data = user.to_dict()
            if user.resident:
                user_data['resident'] = user.resident.to_dict()
            result.append(user_data)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/approve-registration/<user_id>', methods=['POST'])
@jwt_required()
def approve_registration(user_id):
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Update both status and role
        user.status = 'active'
        user.role = 'resident'  # Change from 'pending' to 'resident'
        
        # Send approval email notification and track status
        email_success = False
        email_message = "No email attempt made"
        
        if user.resident:
            email_success, email_message = send_approval_email(user.email, user.resident.first_name)
            user.approval_email_sent = email_success
            user.approval_email_sent_at = datetime.utcnow() if email_success else None
        
        db.session.commit()
        
        return jsonify({
            'message': 'Registration approved successfully',
            'email_sent': email_success,
            'email_status': email_message
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/reject-registration/<user_id>', methods=['POST'])
@jwt_required()
def reject_registration(user_id):
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Send rejection email before deleting user
        email_success = False
        email_message = "No email attempt made"
        
        if user.resident:
            email_success, email_message = send_rejection_email(user.email, user.resident.first_name)
            user.rejection_email_sent = email_success
            user.rejection_email_sent_at = datetime.utcnow() if email_success else None
            db.session.commit()  # Save email status before deletion
        
        # Delete user and associated resident data
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'message': 'Registration rejected and deleted',
            'email_sent': email_success,
            'email_status': email_message
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/residents', methods=['GET'])
@jwt_required()
def get_all_residents():
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        residents = Resident.query.all()
        result = []
        
        for resident in residents:
            resident_data = resident.to_dict()
            resident_data['user'] = resident.user.to_dict()
            
            # Add property information
            if resident.properties:
                resident_data['properties'] = [prop.to_dict() for prop in resident.properties]
            
            # Add vehicle information
            if resident.vehicles:
                resident_data['vehicles'] = [vehicle.to_dict() for vehicle in resident.vehicles]
            
            result.append(resident_data)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/properties', methods=['GET'])
@jwt_required()
def get_all_properties():
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        properties = Property.query.all()
        result = []
        
        for prop in properties:
            prop_data = prop.to_dict()
            
            # Add resident information
            if prop.resident:
                prop_data['resident'] = prop.resident.to_dict()
            
            # Add builder information
            if prop.builder:
                prop_data['builder'] = prop.builder.to_dict()
            
            # Add meter information
            if prop.meters:
                prop_data['meters'] = [meter.to_dict() for meter in prop.meters]
            
            result.append(prop_data)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/properties', methods=['POST'])
@jwt_required()
def create_property():
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        data = request.get_json()
        
        # Check if erf_number already exists
        if Property.query.filter_by(erf_number=data['erf_number']).first():
            return jsonify({'error': 'Property with this erf number already exists'}), 400
        
        property = Property(
            erf_number=data['erf_number'],
            address=data['address'],
            resident_id=data.get('resident_id'),
            plot_registered_date=datetime.strptime(data['plot_registered_date'], '%Y-%m-%d').date() if data.get('plot_registered_date') else None
        )
        
        db.session.add(property)
        db.session.commit()
        
        return jsonify(property.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/builders', methods=['POST'])
@jwt_required()
def create_builder():
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        data = request.get_json()
        
        builder = Builder(
            property_id=data['property_id'],
            company_name=data['company_name'],
            contact_person=data.get('contact_person'),
            contact_number=data.get('contact_number'),
            building_start_date=datetime.strptime(data['building_start_date'], '%Y-%m-%d').date() if data.get('building_start_date') else None,
            building_end_date=datetime.strptime(data['building_end_date'], '%Y-%m-%d').date() if data.get('building_end_date') else None
        )
        
        db.session.add(builder)
        db.session.commit()
        
        return jsonify(builder.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/meters', methods=['POST'])
@jwt_required()
def create_meter():
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        data = request.get_json()
        
        # Check if meter_number already exists
        if Meter.query.filter_by(meter_number=data['meter_number']).first():
            return jsonify({'error': 'Meter with this number already exists'}), 400
        
        meter = Meter(
            property_id=data['property_id'],
            meter_type=data['meter_type'],
            meter_number=data['meter_number'],
            installation_date=datetime.strptime(data['installation_date'], '%Y-%m-%d').date() if data.get('installation_date') else None
        )
        
        db.session.add(meter)
        db.session.commit()
        
        return jsonify(meter.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/complaints', methods=['GET'])
@jwt_required()
def get_all_complaints():
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        complaints = Complaint.query.all()
        result = []
        
        for complaint in complaints:
            complaint_data = complaint.to_dict()
            complaint_data['resident'] = complaint.resident.to_dict()
            
            # Add updates
            if complaint.updates:
                complaint_data['updates'] = [update.to_dict() for update in complaint.updates]
            
            result.append(complaint_data)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/complaints/<complaint_id>/update', methods=['POST'])
@jwt_required()
def update_complaint(complaint_id):
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return jsonify({'error': 'Complaint not found'}), 404
        
        # Update complaint status if provided
        if 'status' in data:
            complaint.status = data['status']
        
        if 'priority' in data:
            complaint.priority = data['priority']
        
        if 'assigned_to' in data:
            complaint.assigned_to = data['assigned_to']
        
        # Add update if provided
        if 'update_text' in data:
            update = ComplaintUpdate(
                complaint_id=complaint_id,
                user_id=user_id,
                update_text=data['update_text']
            )
            db.session.add(update)
        
        db.session.commit()
        
        return jsonify({'message': 'Complaint updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/gate-register', methods=['GET'])
@jwt_required()
def get_gate_register():
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        vehicles = Vehicle.query.join(Resident).join(User).filter(User.status == 'active').all()
        result = []
        
        for vehicle in vehicles:
            vehicle_data = vehicle.to_dict()
            vehicle_data['resident'] = vehicle.resident.to_dict()
            
            # Add property information
            if vehicle.resident.properties:
                vehicle_data['property'] = vehicle.resident.properties[0].to_dict()
            
            result.append(vehicle_data)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/communication/emails', methods=['GET'])
@jwt_required()
def get_resident_emails():
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        users = User.query.filter_by(status='active', role='resident').all()
        emails = [user.email for user in users]
        
        return jsonify({'emails': emails}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/communication/phones', methods=['GET'])
@jwt_required()
def get_resident_phones():
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        residents = Resident.query.join(User).filter(User.status == 'active').all()
        phones = [resident.phone_number for resident in residents if resident.phone_number]
        
        return jsonify({'phones': phones}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/email-status', methods=['GET'])
@jwt_required()
def get_email_status():
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        # Get all users with email status
        users = User.query.all()
        result = []
        
        for user in users:
            email_data = {
                'id': user.id,
                'email': user.email,
                'status': user.status,
                'role': user.role,
                'approval_email_sent': user.approval_email_sent,
                'approval_email_sent_at': user.approval_email_sent_at.isoformat() if user.approval_email_sent_at else None,
                'rejection_email_sent': user.rejection_email_sent,
                'rejection_email_sent_at': user.rejection_email_sent_at.isoformat() if user.rejection_email_sent_at else None,
            }
            
            if user.resident:
                email_data['name'] = f"{user.resident.first_name} {user.resident.last_name}"
            
            result.append(email_data)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

