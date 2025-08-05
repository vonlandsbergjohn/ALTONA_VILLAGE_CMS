from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import text
from src.models.user import User, Resident, Owner, Property, Vehicle, Builder, Meter, Complaint, ComplaintUpdate, ErfAddressMapping, db
from src.utils.email_service import send_approval_email, send_rejection_email
from datetime import datetime
import pandas as pd
import io
import csv
import csv
import io
import os

# Import change tracking function
try:
    from src.routes.admin_notifications import log_user_change
except ImportError:
    # Fallback if admin_notifications module doesn't exist yet
    def log_user_change(*args, **kwargs):
        pass

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
                user_data['erf_number'] = user.resident.erf_number  # Add ERF number for matching
                user_data['first_name'] = user.resident.first_name
                user_data['last_name'] = user.resident.last_name
                user_data['phone_number'] = user.resident.phone_number
                user_data['emergency_contact_name'] = user.resident.emergency_contact_name
                user_data['emergency_contact_number'] = user.resident.emergency_contact_number
                user_data['id_number'] = user.resident.id_number
                user_data['address'] = user.resident.display_address
                user_data['is_owner'] = user.is_owner()
                user_data['is_resident'] = True
            elif user.owner:
                user_data['owner'] = user.owner.to_dict()
                user_data['erf_number'] = user.owner.erf_number  # Add ERF number for matching
                user_data['first_name'] = user.owner.first_name
                user_data['last_name'] = user.owner.last_name
                user_data['phone_number'] = user.owner.phone_number
                user_data['emergency_contact_name'] = user.owner.emergency_contact_name
                user_data['emergency_contact_number'] = user.owner.emergency_contact_number
                user_data['id_number'] = user.owner.id_number
                user_data['address'] = user.owner.display_address
                user_data['is_owner'] = True
                user_data['is_resident'] = user.is_resident()
            result.append(user_data)
        
        return jsonify({
            'data': result,
            'total': len(result)
        }), 200
        
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
        
        # Get the user's first name using the new User method
        first_name = user.get_full_name().split(' ')[0]
        
        # Always attempt to send approval email
        email_success, email_message = send_approval_email(user.email, first_name)
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
        
        # Get the user's first name using the new User method
        first_name = user.get_full_name().split(' ')[0]
        
        # Always attempt to send rejection email
        email_success, email_message = send_rejection_email(user.email, first_name)
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
        # Get all users with either resident or owner records
        users = User.query.filter(
            (User.resident.has()) | (User.owner.has())
        ).all()
        
        result = []
        
        for user in users:
            # Start with user data
            user_data = {
                'user_id': user.id,
                'email': user.email,
                'status': user.status,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'is_resident': user.resident is not None,
                'is_owner': user.owner is not None,
            }
            
            # Add tenant_or_owner status
            if user.resident and user.owner:
                user_data['tenant_or_owner'] = 'owner-resident'
            elif user.owner:
                user_data['tenant_or_owner'] = 'owner'
            elif user.resident:
                user_data['tenant_or_owner'] = 'tenant'
            else:
                user_data['tenant_or_owner'] = ''
            
            # Add resident data if available
            if user.resident:
                resident = user.resident
                user_data.update({
                    'id': resident.id,
                    'first_name': resident.first_name,
                    'last_name': resident.last_name,
                    'phone_number': resident.phone_number,
                    'emergency_contact_name': resident.emergency_contact_name,
                    'emergency_contact_number': resident.emergency_contact_number,
                    'id_number': resident.id_number,
                    'erf_number': resident.erf_number,
                    'street_number': resident.street_number,
                    'street_name': resident.street_name,
                    'full_address': resident.full_address,
                    'intercom_code': resident.intercom_code,
                })
            
            # Add owner data if available (and no resident data)
            elif user.owner:
                owner = user.owner
                user_data.update({
                    'id': owner.id,
                    'first_name': owner.first_name,
                    'last_name': owner.last_name,
                    'phone_number': owner.phone_number,
                    'emergency_contact_name': owner.emergency_contact_name,
                    'emergency_contact_number': owner.emergency_contact_number,
                    'id_number': owner.id_number,
                    'erf_number': owner.erf_number,
                    'street_number': owner.street_number,
                    'street_name': owner.street_name,
                    'full_address': owner.full_address,
                    'intercom_code': owner.intercom_code,
                })
            
            result.append(user_data)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/residents/<user_id>', methods=['PUT'])
@jwt_required()
def update_resident(user_id):
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Find the user
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Capture old values BEFORE making changes for change tracking
        old_values = {}
        
        # Capture old values for comparison
        if 'full_name' in data:
            if user.resident:
                old_values['full_name'] = f"{user.resident.first_name} {user.resident.last_name}".strip()
            elif user.owner:
                old_values['full_name'] = f"{user.owner.first_name} {user.owner.last_name}".strip()
            else:
                old_values['full_name'] = ""
        
        if 'phone' in data:
            old_values['phone'] = user.resident.phone_number if user.resident else (user.owner.phone_number if user.owner else '')
        
        if 'email' in data:
            old_values['email'] = user.email
            
        if 'intercom_code' in data:
            old_values['intercom_code'] = user.resident.intercom_code if user.resident else (user.owner.intercom_code if user.owner else '')
            
        if 'property_address' in data:
            old_values['property_address'] = user.resident.full_address if user.resident else (user.owner.full_address if user.owner else '')
        
        if 'resident_status_change' in data or 'tenant_or_owner' in data:
            old_values['resident_status'] = 'Owner-Resident' if (user.resident and user.owner) else ('Resident' if user.resident else 'Owner')
        
        # Update user basic info
        if 'email' in data:
            # Check if email is already in use by another user
            existing_user = User.query.filter(User.email == data['email'], User.id != user_id).first()
            if existing_user:
                return jsonify({'error': 'Email already in use'}), 400
            user.email = data['email']
        
        # Update resident information if user has resident record
        if user.resident:
            resident = user.resident
            
            if 'full_name' in data:
                # Split full name into first and last name
                names = data['full_name'].strip().split(' ', 1)
                resident.first_name = names[0]
                resident.last_name = names[1] if len(names) > 1 else ''
            
            if 'phone' in data:
                resident.phone_number = data['phone']
            
            if 'emergency_contact_name' in data:
                resident.emergency_contact_name = data['emergency_contact_name']
            
            if 'emergency_contact_phone' in data:
                resident.emergency_contact_number = data['emergency_contact_phone']
            
            if 'intercom_code' in data:
                resident.intercom_code = data['intercom_code']
            
            if 'property_address' in data:
                # Parse the address and update components
                from src.routes.auth import parse_address
                street_number, street_name = parse_address(data['property_address'])
                resident.street_number = street_number
                resident.street_name = street_name
                resident.full_address = data['property_address']
        
        # Update owner information if user has owner record
        if user.owner:
            owner = user.owner
            
            if 'full_name' in data:
                # Split full name into first and last name
                names = data['full_name'].strip().split(' ', 1)
                owner.first_name = names[0]
                owner.last_name = names[1] if len(names) > 1 else ''
            
            if 'phone' in data:
                owner.phone_number = data['phone']
            
            if 'emergency_contact_name' in data:
                owner.emergency_contact_name = data['emergency_contact_name']
            
            if 'emergency_contact_phone' in data:
                owner.emergency_contact_number = data['emergency_contact_phone']
            
            if 'intercom_code' in data:
                owner.intercom_code = data['intercom_code']
            
            if 'property_address' in data:
                # Parse the address and update components
                from src.routes.auth import parse_address
                street_number, street_name = parse_address(data['property_address'])
                owner.street_number = street_number
                owner.street_name = street_name
                owner.full_address = data['property_address']
        
        # Handle resident status change (support both field names for compatibility)  
        if 'resident_status_change' in data or 'tenant_or_owner' in data:
            new_status = data.get('resident_status_change') or data.get('tenant_or_owner')
            
            # Map frontend status names to backend values
            status_mapping = {
                'Property Owner': 'owner',
                'property owner': 'owner',
                'Owner': 'owner',
                'owner': 'owner',
                'Tenant': 'tenant',
                'tenant': 'tenant',
                'Resident': 'tenant',
                'resident': 'tenant',
                'Owner-Resident': 'owner-resident',
                'owner-resident': 'owner-resident',
                'Property Owner-Resident': 'owner-resident'
            }
            
            # Use mapped status or original if not found
            new_status = status_mapping.get(new_status, new_status)
            
            current_is_resident = user.resident is not None
            current_is_owner = user.owner is not None
            
            # Get name components for new records
            if 'full_name' in data:
                names = data['full_name'].strip().split(' ', 1)
                first_name = names[0]
                last_name = names[1] if len(names) > 1 else ''
            else:
                # Use existing names from current records
                if user.resident:
                    first_name = user.resident.first_name
                    last_name = user.resident.last_name
                elif user.owner:
                    first_name = user.owner.first_name
                    last_name = user.owner.last_name
                else:
                    first_name = ''
                    last_name = ''
            
            # Handle different status changes
            if new_status == 'resident' or new_status == 'tenant':
                # Ensure resident record exists
                if not current_is_resident:
                    resident = Resident(
                        user_id=user.id,
                        first_name=first_name,
                        last_name=last_name,
                        phone_number=data.get('phone', user.owner.phone_number if user.owner else ''),
                        emergency_contact_name=data.get('emergency_contact_name', user.owner.emergency_contact_name if user.owner else ''),
                        emergency_contact_number=data.get('emergency_contact_phone', user.owner.emergency_contact_number if user.owner else ''),
                        intercom_code=data.get('intercom_code', user.owner.intercom_code if user.owner else ''),
                        id_number=user.owner.id_number if user.owner and user.owner.id_number else 'TEMP_ID',
                        erf_number=user.owner.erf_number if user.owner and user.owner.erf_number else 'TEMP_ERF',
                        street_number=user.owner.street_number if user.owner else '',
                        street_name=user.owner.street_name if user.owner else '',
                        full_address=data.get('property_address', user.owner.full_address if user.owner else '')
                    )
                    db.session.add(resident)
                    db.session.flush()  # Flush to get the resident.id
                
                # Remove owner record if changing to tenant/resident only
                if current_is_owner:
                    # Before deleting owner record, reassign any vehicles to the resident record
                    old_owner_vehicles = Vehicle.query.filter_by(owner_id=user.owner.id).all()
                    for vehicle in old_owner_vehicles:
                        vehicle.owner_id = None
                        # Use the correct resident ID - either newly created or existing
                        target_resident_id = resident.id if not current_is_resident else user.resident.id
                        vehicle.resident_id = target_resident_id
                    
                    db.session.delete(user.owner)
            
            elif new_status == 'owner':
                # Ensure owner record exists
                if not current_is_owner:
                    owner = Owner(
                        user_id=user.id,
                        first_name=first_name,
                        last_name=last_name,
                        phone_number=data.get('phone', user.resident.phone_number if user.resident else ''),
                        emergency_contact_name=data.get('emergency_contact_name', user.resident.emergency_contact_name if user.resident else ''),
                        emergency_contact_number=data.get('emergency_contact_phone', user.resident.emergency_contact_number if user.resident else ''),
                        intercom_code=data.get('intercom_code', user.resident.intercom_code if user.resident else ''),
                        id_number=user.resident.id_number if user.resident and user.resident.id_number else 'TEMP_ID',
                        erf_number=user.resident.erf_number if user.resident and user.resident.erf_number else 'TEMP_ERF',
                        street_number=user.resident.street_number if user.resident else '',
                        street_name=user.resident.street_name if user.resident else '',
                        full_address=data.get('property_address', user.resident.full_address if user.resident else '')
                    )
                    db.session.add(owner)
                    db.session.flush()  # Flush to get the owner.id
                
                # Remove resident record if changing to owner only
                if current_is_resident:
                    # Before deleting resident record, reassign any vehicles to the owner record  
                    old_resident_vehicles = Vehicle.query.filter_by(resident_id=user.resident.id).all()
                    for vehicle in old_resident_vehicles:
                        vehicle.resident_id = None
                        # Use the correct owner ID - either newly created or existing
                        target_owner_id = owner.id if not current_is_owner else user.owner.id
                        vehicle.owner_id = target_owner_id
                    
                    db.session.delete(user.resident)
            
            elif new_status == 'owner-resident':
                # Ensure both records exist
                if not current_is_resident:
                    resident = Resident(
                        user_id=user.id,
                        first_name=first_name,
                        last_name=last_name,
                        phone_number=data.get('phone', user.owner.phone_number if user.owner else ''),
                        emergency_contact_name=data.get('emergency_contact_name', user.owner.emergency_contact_name if user.owner else ''),
                        emergency_contact_number=data.get('emergency_contact_phone', user.owner.emergency_contact_number if user.owner else ''),
                        intercom_code=data.get('intercom_code', user.owner.intercom_code if user.owner else ''),
                        id_number=user.owner.id_number if user.owner and user.owner.id_number else 'TEMP_ID',
                        erf_number=user.owner.erf_number if user.owner and user.owner.erf_number else 'TEMP_ERF',
                        street_number=user.owner.street_number if user.owner else '',
                        street_name=user.owner.street_name if user.owner else '',
                        full_address=data.get('property_address', user.owner.full_address if user.owner else '')
                    )
                    db.session.add(resident)
                
                if not current_is_owner:
                    owner = Owner(
                        user_id=user.id,
                        first_name=first_name,
                        last_name=last_name,
                        phone_number=data.get('phone', user.resident.phone_number if user.resident else ''),
                        emergency_contact_name=data.get('emergency_contact_name', user.resident.emergency_contact_name if user.resident else ''),
                        emergency_contact_number=data.get('emergency_contact_phone', user.resident.emergency_contact_number if user.resident else ''),
                        intercom_code=data.get('intercom_code', user.resident.intercom_code if user.resident else ''),
                        id_number=user.resident.id_number if user.resident and user.resident.id_number else 'TEMP_ID',
                        erf_number=user.resident.erf_number if user.resident and user.resident.erf_number else 'TEMP_ERF',
                        street_number=user.resident.street_number if user.resident else '',
                        street_name=user.resident.street_name if user.resident else '',
                        full_address=data.get('property_address', user.resident.full_address if user.resident else '')
                    )
                    db.session.add(owner)
                
                # For owner-resident status, vehicles can be associated with either record
                # We'll keep them as they are but ensure they show up in queries
        
        # Log changes for admin change tracking
        try:
            # Get user display name and ERF number for logging
            if user.resident:
                user_name = f"{user.resident.first_name} {user.resident.last_name}".strip()
                erf_number = user.resident.erf_number or 'Unknown'
            elif user.owner:
                user_name = f"{user.owner.first_name} {user.owner.last_name}".strip()
                erf_number = user.owner.erf_number or 'Unknown'
            else:
                user_name = user.email
                erf_number = 'Unknown'
            
            # Log changes made by admin - only if values actually changed
            if 'full_name' in data and old_values.get('full_name') != data['full_name']:
                log_user_change(user.id, user_name, erf_number, 'admin_update', 'full_name', old_values['full_name'], data['full_name'])
            
            if 'phone' in data and old_values.get('phone') != data['phone']:
                log_user_change(user.id, user_name, erf_number, 'admin_update', 'cellphone_number', old_values['phone'], data['phone'])
            
            if 'email' in data and old_values.get('email') != data['email']:
                log_user_change(user.id, user_name, erf_number, 'admin_update', 'email', old_values['email'], data['email'])
            
            if 'intercom_code' in data and old_values.get('intercom_code') != data['intercom_code']:
                log_user_change(user.id, user_name, erf_number, 'admin_update', 'intercom_code', old_values['intercom_code'], data['intercom_code'])
            
            if 'property_address' in data and old_values.get('property_address') != data['property_address']:
                log_user_change(user.id, user_name, erf_number, 'admin_update', 'property_address', old_values['property_address'], data['property_address'])
            
            if ('resident_status_change' in data or 'tenant_or_owner' in data):
                new_status = data.get('resident_status_change') or data.get('tenant_or_owner')
                if old_values.get('resident_status') != new_status:
                    log_user_change(user.id, user_name, erf_number, 'admin_update', 'resident_status', old_values['resident_status'], new_status)
                
        except Exception as log_error:
            print(f"Error logging admin change: {log_error}")
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Resident updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
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
        # Use similar logic to the export function to ensure consistency
        active_users = User.query.filter(User.status.in_(['active', 'approved'])).all()
        result = []
        
        for user in active_users:
            if user.role == 'admin':
                continue
            
            resident_data = None
            owner_data = None
            status = 'Unknown'
            
            # Determine user status and get appropriate data
            if user.resident and user.owner:
                status = 'Owner-Resident'
                resident_data = user.resident
                owner_data = user.owner
            elif user.resident:
                status = 'Resident'
                resident_data = user.resident
            elif user.owner:
                status = 'Owner'
                owner_data = user.owner
            
            primary_data = resident_data if resident_data else owner_data
            
            if not primary_data:
                continue
            
            # Additional check: Only include residents/owners with active or approved status
            # For Owner-Residents, check both records are active
            if resident_data and resident_data.status not in ['active', 'approved']:
                continue
            if owner_data and owner_data.status not in ['active', 'approved']:
                continue
            
            # Get vehicle registrations for this user
            vehicle_registrations = []
            if resident_data:
                vehicles = Vehicle.query.filter_by(resident_id=resident_data.id).all()
                vehicle_registrations = [v.registration_number for v in vehicles]
            elif owner_data:
                vehicles = Vehicle.query.filter_by(owner_id=owner_data.id).all()
                vehicle_registrations = [v.registration_number for v in vehicles]
            
            # Create entry with all user information and their vehicles
            entry = {
                'user_id': user.id,
                'resident_status': status,
                'first_name': primary_data.first_name or '',
                'last_name': primary_data.last_name or '',
                'surname': primary_data.last_name or '',  # For compatibility
                'street_number': primary_data.street_number or '',
                'street_name': primary_data.street_name or '',
                'full_address': primary_data.full_address or '',
                'erf_number': primary_data.erf_number or '',
                'intercom_code': primary_data.intercom_code or '',
                'phone_number': primary_data.phone_number or '',
                'vehicle_registrations': vehicle_registrations,
                'total_vehicles': len(vehicle_registrations),
                'email': user.email,
                'sort_key': (primary_data.street_name or '').upper()
            }
            
            result.append(entry)
        
        # Sort by street name alphabetically (same as export)
        result.sort(key=lambda x: x['sort_key'])
        
        # Calculate total vehicles across all users
        total_vehicles = sum(len(entry['vehicle_registrations']) for entry in result)
        
        return jsonify({
            'success': True,
            'data': result,
            'count': len(result),
            'total_vehicles': total_vehicles
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/gate-register/export', methods=['GET'])
@jwt_required()
def export_gate_register():
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        # Use the same logic as the gate register API but format for CSV export
        active_users = User.query.filter_by(status='active').all()
        gate_entries = []
        
        for user in active_users:
            if user.role == 'admin':
                continue
            
            resident_data = None
            owner_data = None
            status = 'Unknown'
            
            # Determine user status and get appropriate data
            if user.resident and user.owner:
                status = 'Owner-Resident'
                resident_data = user.resident
                owner_data = user.owner
            elif user.resident:
                status = 'Resident'
                resident_data = user.resident
            elif user.owner:
                status = 'Owner'
                owner_data = user.owner
            
            primary_data = resident_data if resident_data else owner_data
            
            if not primary_data:
                continue
            
            # Get vehicle registrations for this user
            vehicle_registrations = []
            if resident_data:
                vehicles = Vehicle.query.filter_by(resident_id=resident_data.id).all()
                vehicle_registrations = [v.registration_number for v in vehicles]
            elif owner_data:
                vehicles = Vehicle.query.filter_by(owner_id=owner_data.id).all()
                vehicle_registrations = [v.registration_number for v in vehicles]
            
            # Handle multiple vehicles - create separate row for each vehicle
            if vehicle_registrations:
                for vehicle_reg in vehicle_registrations:
                    entry = {
                        'resident_status': status,
                        'surname': primary_data.last_name or '',
                        'street_number': str(primary_data.street_number or ''),
                        'street_name': primary_data.street_name or '',
                        'vehicle_registration': vehicle_reg,
                        'erf_number': str(primary_data.erf_number or ''),
                        'intercom_code': str(primary_data.intercom_code or ''),
                        'sort_key': (primary_data.street_name or '').upper()
                    }
                    gate_entries.append(entry)
            else:
                # No vehicles - still include the resident/owner
                entry = {
                    'resident_status': status,
                    'surname': primary_data.last_name or '',
                    'street_number': str(primary_data.street_number or ''),
                    'street_name': primary_data.street_name or '',
                    'vehicle_registration': '',
                    'erf_number': str(primary_data.erf_number or ''),
                    'intercom_code': str(primary_data.intercom_code or ''),
                    'sort_key': (primary_data.street_name or '').upper()
                }
                gate_entries.append(entry)
        
        # Sort by street name alphabetically
        gate_entries.sort(key=lambda x: x['sort_key'])
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'RESIDENT STATUS',
            'SURNAME', 
            'STREET NR',
            'STREET NAME',
            'VEHICLE REGISTRATION NR',
            'ERF NR',
            'INTERCOM NR'
        ])
        
        # Write data rows
        for entry in gate_entries:
            writer.writerow([
                entry['resident_status'],
                entry['surname'],
                entry['street_number'],
                entry['street_name'],
                entry['vehicle_registration'],
                entry['erf_number'],
                entry['intercom_code']
            ])
        
        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f'gate_register_{timestamp}.csv'
        
        # Create response
        output.seek(0)
        csv_content = output.getvalue()
        output.close()
        
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Type': 'text/csv; charset=utf-8'
            }
        )
        
    except Exception as e:
        return jsonify({'error': f'Failed to export gate register: {str(e)}'}), 500

@admin_bp.route('/gate-register/changes', methods=['GET'])
@jwt_required()
def get_gate_register_changes():
    """Get gate register data with change tracking for notification system"""
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        # Get all users with changes from the user_changes table
        import sqlite3
        db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'app.db')
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Get users who have unreviewed changes
            cursor.execute("""
                SELECT DISTINCT user_id, field_name, new_value, old_value, change_timestamp
                FROM user_changes 
                WHERE admin_reviewed = 0
                ORDER BY change_timestamp DESC
            """)
            
            user_changes = cursor.fetchall()
        
        if not user_changes:
            return jsonify({
                'success': True,
                'data': [],
                'count': 0,
                'message': 'No pending changes found'
            }), 200
        
        # Group changes by user_id and classify them
        changes_by_user = {}
        critical_fields = ['cellphone_number', 'vehicle_registration', 'vehicle_registration_2']
        
        for change in user_changes:
            user_id, field_name, new_value, old_value, timestamp = change
            if user_id not in changes_by_user:
                changes_by_user[user_id] = {}
            
            is_critical = field_name in critical_fields
            changes_by_user[user_id][field_name] = {
                'new_value': new_value,
                'old_value': old_value,
                'timestamp': timestamp,
                'changed': True,
                'is_critical': is_critical
            }
        
        # Get gate register data for users with changes
        result = []
        user_ids = list(changes_by_user.keys())
        
        # Convert string UUIDs to proper format for querying
        for user_uuid in user_ids:
            user = User.query.filter_by(id=user_uuid).first()
            if not user or user.role == 'admin':
                continue
                
            resident_data = None
            owner_data = None
            status = 'Unknown'
            
            # Determine user status and get appropriate data
            if user.resident and user.owner:
                status = 'Owner-Resident'
                resident_data = user.resident
                owner_data = user.owner
            elif user.resident:
                status = 'Resident'
                resident_data = user.resident
            elif user.owner:
                status = 'Owner'
                owner_data = user.owner
            else:
                continue
            
            # Use the primary data source (resident takes priority)
            primary_data = resident_data if resident_data else owner_data
            if not primary_data:
                continue
            
            # Get vehicles
            vehicle_registrations = []
            if resident_data:
                vehicles = Vehicle.query.filter_by(resident_id=resident_data.id).all()
                vehicle_registrations = [v.registration_number for v in vehicles]
            elif owner_data:
                vehicles = Vehicle.query.filter_by(owner_id=owner_data.id).all()
                vehicle_registrations = [v.registration_number for v in vehicles]
            
            # Get changes for this user
            user_change_info = changes_by_user.get(user_uuid, {})
            
            # Check if phone number was changed
            phone_changed = 'cellphone_number' in user_change_info
            current_phone = user_change_info.get('cellphone_number', {}).get('new_value', primary_data.phone_number or '')
            
            # Check if any vehicle registrations were changed
            vehicle_changes = [change for field, change in user_change_info.items() if 'vehicle_registration' in field]
            
            if vehicle_registrations:
                # Create entry for each vehicle
                for i, vehicle_reg in enumerate(vehicle_registrations):
                    # Check if this specific vehicle was changed
                    vehicle_changed = any(change['new_value'] == vehicle_reg for change in vehicle_changes)
                    
                    entry = {
                        'user_id': user.id,
                        'resident_status': status,
                        'first_name': primary_data.first_name or '',
                        'last_name': primary_data.last_name or '',
                        'surname': primary_data.last_name or '',
                        'street_number': primary_data.street_number or '',
                        'street_name': primary_data.street_name or '',
                        'full_address': primary_data.full_address or '',
                        'erf_number': primary_data.erf_number or '',
                        'intercom_code': primary_data.intercom_code or '',
                        'phone_number': current_phone,
                        'vehicle_registration': vehicle_reg,
                        'email': user.email,
                        'sort_key': (primary_data.street_name or '').upper(),
                        # Change tracking flags
                        'phone_changed': phone_changed and i == 0,  # Only show phone change on first vehicle entry
                        'vehicle_changed': vehicle_changed,
                        'changes_info': user_change_info if i == 0 else {}  # Only include change info on first entry
                    }
                    result.append(entry)
            else:
                # No vehicles - still include the resident/owner
                entry = {
                    'user_id': user.id,
                    'resident_status': status,
                    'first_name': primary_data.first_name or '',
                    'last_name': primary_data.last_name or '',
                    'surname': primary_data.last_name or '',
                    'street_number': primary_data.street_number or '',
                    'street_name': primary_data.street_name or '',
                    'full_address': primary_data.full_address or '',
                    'erf_number': primary_data.erf_number or '',
                    'intercom_code': primary_data.intercom_code or '',
                    'phone_number': current_phone,
                    'vehicle_registration': '',
                    'email': user.email,
                    'sort_key': (primary_data.street_name or '').upper(),
                    # Change tracking flags
                    'phone_changed': phone_changed,
                    'vehicle_changed': False,
                    'changes_info': user_change_info
                }
                result.append(entry)
        
        # Sort by street name alphabetically
        result.sort(key=lambda x: x['sort_key'])
        
        return jsonify({
            'success': True,
            'data': result,
            'count': len(result),
            'total_changes': len(user_changes)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get gate register changes: {str(e)}'}), 500

@admin_bp.route('/gate-register/export-changes', methods=['GET'])
@jwt_required()
def export_gate_register_changes():
    """Export gate register with only changed users and red highlighting for changed fields"""
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        # Get gate register changes data
        import sqlite3
        db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'app.db')
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Get users who have unreviewed changes
            cursor.execute("""
                SELECT DISTINCT user_id, field_name, new_value, old_value, change_timestamp
                FROM user_changes 
                WHERE admin_reviewed = 0
                ORDER BY change_timestamp DESC
            """)
            
            user_changes = cursor.fetchall()
        
        if not user_changes:
            return jsonify({'error': 'No pending changes found to export'}), 404
        
        # Group changes by user_id and classify them
        changes_by_user = {}
        critical_fields = ['cellphone_number', 'vehicle_registration', 'vehicle_registration_2']
        
        for change in user_changes:
            user_id, field_name, new_value, old_value, timestamp = change
            if user_id not in changes_by_user:
                changes_by_user[user_id] = {}
            
            is_critical = field_name in critical_fields
            changes_by_user[user_id][field_name] = {
                'new_value': new_value,
                'old_value': old_value,
                'timestamp': timestamp,
                'changed': True,
                'is_critical': is_critical
            }
        
        # Create CSV with change highlighting (HTML format for red backgrounds)
        output = io.StringIO()
        
        # Create HTML table instead of CSV for proper red background formatting
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Gate Register - Changes Only</title>
    <style>
        table { border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; font-weight: bold; }
        .critical-changed { background-color: #ff6b6b !important; color: white; font-weight: bold; }
        .non-critical-changed { background-color: #4CAF50 !important; color: white; font-weight: bold; }
        .header { background-color: #2196F3; color: white; }
    </style>
</head>
<body>
    <h1>Altona Village - Gate Register Changes</h1>
    <p>Generated: """ + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC') + """</p>
    <p>This document shows only residents/owners with recent changes. Changed information is highlighted in red.</p>
    
    <table>
        <tr class="header">
            <th>RESIDENT STATUS</th>
            <th>FIRST NAME</th>
            <th>SURNAME</th>
            <th>PHONE NUMBER</th>
            <th>STREET NR</th>
            <th>STREET NAME</th>
            <th>VEHICLE REGISTRATION NR</th>
            <th>ERF NR</th>
            <th>INTERCOM NR</th>
        </tr>
"""
        
        # Get gate register data for users with changes
        user_ids = list(changes_by_user.keys())
        
        # Convert string UUIDs to proper format for querying
        for user_uuid in user_ids:
            user = User.query.filter_by(id=user_uuid).first()
            if not user or user.role == 'admin':
                continue
                
            resident_data = None
            owner_data = None
            status = 'Unknown'
            
            # Determine user status and get appropriate data
            if user.resident and user.owner:
                status = 'Owner-Resident'
                resident_data = user.resident
                owner_data = user.owner
            elif user.resident:
                status = 'Resident'
                resident_data = user.resident
            elif user.owner:
                status = 'Owner'
                owner_data = user.owner
            else:
                continue
            
            # Use the primary data source (resident takes priority)
            primary_data = resident_data if resident_data else owner_data
            if not primary_data:
                continue
            
            # Get vehicles
            vehicle_registrations = []
            if resident_data:
                vehicles = Vehicle.query.filter_by(resident_id=resident_data.id).all()
                vehicle_registrations = [v.registration_number for v in vehicles]
            elif owner_data:
                vehicles = Vehicle.query.filter_by(owner_id=owner_data.id).all()
                vehicle_registrations = [v.registration_number for v in vehicles]
            
            # Get changes for this user
            user_change_info = changes_by_user.get(user_uuid, {})
            
            # Check if phone number was changed (critical)
            phone_change_info = user_change_info.get('cellphone_number', {})
            phone_changed = 'cellphone_number' in user_change_info
            current_phone = phone_change_info.get('new_value', primary_data.phone_number or '')
            phone_is_critical = phone_change_info.get('is_critical', True)
            
            # Check if intercom code was changed (non-critical)
            intercom_change_info = user_change_info.get('intercom_code', {})
            intercom_changed = 'intercom_code' in user_change_info
            current_intercom = intercom_change_info.get('new_value', primary_data.intercom_code or '')
            intercom_is_critical = intercom_change_info.get('is_critical', False)
            
            # Check if any vehicle registrations were changed (critical)
            vehicle_changes = [change for field, change in user_change_info.items() if 'vehicle_registration' in field]
            
            if vehicle_registrations:
                # Create entry for each vehicle
                for i, vehicle_reg in enumerate(vehicle_registrations):
                    # Check if this specific vehicle was changed
                    vehicle_changed = any(change['new_value'] == vehicle_reg for change in vehicle_changes)
                    
                    # Determine CSS classes based on change type
                    phone_class = ''
                    if phone_changed and i == 0:
                        phone_class = 'critical-changed' if phone_is_critical else 'non-critical-changed'
                    
                    vehicle_class = 'critical-changed' if vehicle_changed else ''
                    
                    intercom_class = ''
                    if intercom_changed and i == 0:
                        intercom_class = 'non-critical-changed' if not intercom_is_critical else 'critical-changed'
                    
                    html_content += f"""
        <tr>
            <td>{status}</td>
            <td>{primary_data.first_name or ''}</td>
            <td>{primary_data.last_name or ''}</td>
            <td class="{phone_class}">{current_phone}</td>
            <td>{primary_data.street_number or ''}</td>
            <td>{primary_data.street_name or ''}</td>
            <td class="{vehicle_class}">{vehicle_reg}</td>
            <td>{primary_data.erf_number or ''}</td>
            <td class="{intercom_class}">{current_intercom}</td>
        </tr>"""
            else:
                # No vehicles - still include the resident/owner
                phone_class = ''
                if phone_changed:
                    phone_class = 'critical-changed' if phone_is_critical else 'non-critical-changed'
                
                intercom_class = ''
                if intercom_changed:
                    intercom_class = 'non-critical-changed' if not intercom_is_critical else 'critical-changed'
                
                html_content += f"""
        <tr>
            <td>{status}</td>
            <td>{primary_data.first_name or ''}</td>
            <td>{primary_data.last_name or ''}</td>
            <td class="{phone_class}">{current_phone}</td>
            <td>{primary_data.street_number or ''}</td>
            <td>{primary_data.street_name or ''}</td>
            <td></td>
            <td>{primary_data.erf_number or ''}</td>
            <td class="{intercom_class}">{current_intercom}</td>
        </tr>"""
        
        html_content += """
    </table>
    
    <h2>Change Summary</h2>
    <ul>"""
        
        # Add change summary with color coding
        critical_changes = []
        non_critical_changes = []
        
        for user_uuid, changes in changes_by_user.items():
            user = User.query.filter_by(id=user_uuid).first()
            if user:
                for field, change_info in changes.items():
                    change_text = f"<strong>{user.email}</strong> - {field}: Changed from \"{change_info['old_value']}\" to \"{change_info['new_value']}\""
                    
                    if change_info.get('is_critical', False):
                        critical_changes.append(change_text)
                    else:
                        non_critical_changes.append(change_text)
        
        # Display critical changes
        if critical_changes:
            html_content += """
    <h3 style="color: #ff6b6b;">Critical Changes (Red)</h3>
    <ul>"""
            for change in critical_changes:
                html_content += f"""
        <li style="color: #ff6b6b;">{change}</li>"""
            html_content += """
    </ul>"""
        
        # Display non-critical changes
        if non_critical_changes:
            html_content += """
    <h3 style="color: #4CAF50;">Non-Critical Changes (Green)</h3>
    <ul>"""
            for change in non_critical_changes:
                html_content += f"""
        <li style="color: #4CAF50;">{change}</li>"""
            html_content += """
    </ul>"""
        
        html_content += """
    </ul>
</body>
</html>"""
        
        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f'gate_register_changes_{timestamp}.html'
        
        # Create response
        return Response(
            html_content,
            mimetype='text/html',
            headers={
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Type': 'text/html; charset=utf-8'
            }
        )
        
    except Exception as e:
        return jsonify({'error': f'Failed to export gate register changes: {str(e)}'}), 500

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

@admin_bp.route('/changes/<change_id>/mark-processed', methods=['POST'])
@jwt_required()
def mark_change_processed(change_id):
    """Mark a change as processed by admin"""
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        # Parse the change_id (format: user_id-field_name)
        if '-' not in change_id:
            return jsonify({'error': 'Invalid change ID format'}), 400
            
        # Split the change_id - UUID has 4 dashes, so we need to find the 5th dash
        parts = change_id.split('-')
        
        if len(parts) < 6:  # UUID (5 parts) + field_name (at least 1 part)
            return jsonify({'error': 'Invalid change ID format'}), 400
            
        # First 5 parts are the UUID, rest is field_name
        user_id = '-'.join(parts[:5])  # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        field_name = '-'.join(parts[5:])  # Everything after UUID
        
        # Update the change record in database
        import sqlite3
        db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'app.db')
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # First check if the change exists
            cursor.execute("""
                SELECT id FROM user_changes 
                WHERE user_id = ? AND field_name = ? AND admin_reviewed = 0
                ORDER BY change_timestamp DESC
                LIMIT 1
            """, (user_id, field_name))
            
            result = cursor.fetchone()
            
            if not result:
                return jsonify({'error': 'Change not found or already processed'}), 404
            
            # Mark the most recent unreviewed change for this user and field as reviewed
            cursor.execute("""
                UPDATE user_changes 
                SET admin_reviewed = 1 
                WHERE id = (
                    SELECT id FROM user_changes 
                    WHERE user_id = ? AND field_name = ? AND admin_reviewed = 0
                    ORDER BY change_timestamp DESC
                    LIMIT 1
                )
            """, (user_id, field_name))
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Change not found or already processed'}), 404
            
            conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Change marked as processed'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
        
    except Exception as e:
        return jsonify({'error': f'Failed to mark change as processed: {str(e)}'}), 500

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

# Multi-Group Communication Endpoints
@admin_bp.route('/communication/residents-group', methods=['GET'])
@jwt_required()
def get_residents_group():
    """Get all users who are residents (including owner-residents)"""
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        # Get all users with resident records
        users = User.query.join(Resident).filter(User.status == 'active').all()
        result = []
        
        for user in users:
            group_data = {
                'id': user.id,
                'email': user.email,
                'name': user.get_full_name(),
                'type': 'Owner-Resident' if user.is_owner_resident() else 'Resident',
                'is_resident': True,
                'is_owner': user.is_owner(),
                'is_owner_resident': user.is_owner_resident(),
                'erf_number': user.resident.erf_number if user.resident else None,
                'address': user.resident.address if user.resident else None
            }
            result.append(group_data)
        
        return jsonify({
            'group': 'residents',
            'description': 'All residents (including owner-residents)',
            'count': len(result),
            'members': result
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/communication/owners-group', methods=['GET'])
@jwt_required()
def get_owners_group():
    """Get all users who are owners (including owner-residents)"""
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        # Get all users with owner records
        users = User.query.join(Owner).filter(User.status == 'active').all()
        result = []
        
        for user in users:
            group_data = {
                'id': user.id,
                'email': user.email,
                'name': user.get_full_name(),
                'type': 'Owner-Resident' if user.is_owner_resident() else 'Owner',
                'is_resident': user.is_resident(),
                'is_owner': True,
                'is_owner_resident': user.is_owner_resident(),
                'erf_number': user.owner.erf_number if user.owner else None,
                'address': user.owner.address if user.owner else None,
                'postal_address': user.owner.postal_address if user.owner else None
            }
            result.append(group_data)
        
        return jsonify({
            'group': 'owners',
            'description': 'All owners (including owner-residents)', 
            'count': len(result),
            'members': result
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/communication/non-resident-owners', methods=['GET'])
@jwt_required()
def get_non_resident_owners():
    """Get all users who are owners but not residents"""
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        # Get users who have owner record but no resident record
        users = User.query.join(Owner).outerjoin(Resident).filter(
            User.status == 'active',
            Resident.id == None  # No resident record
        ).all()
        result = []
        
        for user in users:
            group_data = {
                'id': user.id,
                'email': user.email,
                'name': user.get_full_name(),
                'type': 'Owner',
                'is_resident': False,
                'is_owner': True,
                'is_owner_resident': False,
                'erf_number': user.owner.erf_number if user.owner else None,
                'address': user.owner.address if user.owner else None,
                'postal_address': user.owner.postal_address if user.owner else None
            }
            result.append(group_data)
        
        return jsonify({
            'group': 'non-resident-owners',
            'description': 'Owners who are not residents',
            'count': len(result), 
            'members': result
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/communication/owner-residents', methods=['GET'])
@jwt_required()
def get_owner_residents():
    """Get all users who are both owners and residents"""
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        # Get users who have both owner and resident records
        users = User.query.join(Owner).join(Resident).filter(User.status == 'active').all()
        result = []
        
        for user in users:
            group_data = {
                'id': user.id,
                'email': user.email,
                'name': user.get_full_name(),
                'type': 'Owner-Resident',
                'is_resident': True,
                'is_owner': True,
                'is_owner_resident': True,
                'erf_number': user.resident.erf_number if user.resident else None,
                'address': user.resident.address if user.resident else None,
                'postal_address': user.owner.postal_address if user.owner else None
            }
            result.append(group_data)
        
        return jsonify({
            'group': 'owner-residents',
            'description': 'Users who are both owners and residents',
            'count': len(result),
            'members': result
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/communication/groups-summary', methods=['GET'])
@jwt_required()
def get_groups_summary():
    """Get summary of all user groups"""
    try:
        # Get counts for all groups
        residents_count = db.session.query(User).join(Resident).filter(User.status == 'active').count()
        owners_count = db.session.query(User).join(Owner).filter(User.status == 'active').count()
        owner_residents_count = db.session.query(User).join(Resident).join(Owner).filter(User.status == 'active').count()
        non_resident_owners_count = owners_count - owner_residents_count
        
        # Get gate access register info
        gate_register = db.session.execute(text("SELECT * FROM gate_access_register")).fetchall()
        
        summary = {
            'total_residents': residents_count,
            'total_owners': owners_count,
            'owner_residents': owner_residents_count,
            'non_resident_owners': non_resident_owners_count,
            'gate_register_entries': len(gate_register),
            'gate_register_sample': [
                {
                    'last_name': row[0],
                    'first_name': row[1], 
                    'street_name': row[2],
                    'street_number': row[3],
                    'erf_number': row[4],
                    'phone_number': row[5],
                    'email': row[6],
                    'resident_type': row[7],
                    'is_owner': row[8]
                } for row in gate_register[:10]  # First 10 entries
            ]
        }
        
        return jsonify(summary), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/gate-access-register', methods=['GET'])
@jwt_required()
def get_gate_access_register():
    """Get the complete gate access register sorted for security use"""
    try:
        # Query the gate access view
        gate_register = db.session.execute(text("SELECT * FROM gate_access_register")).fetchall()
        
        register_data = [
            {
                'last_name': row[0],
                'first_name': row[1],
                'street_name': row[2],
                'street_number': row[3],
                'erf_number': row[4],
                'phone_number': row[5],
                'email': row[6],
                'resident_type': row[7],
                'is_owner': row[8],
                'full_name': f"{row[1]} {row[0]}",  # First Last
                'display_address': f"{row[2]} {row[3]}",  # Street Name + Number
                'sortable_address': f"{row[2]}_{int(row[3]) if row[3].isdigit() else 999:03d}"  # For proper sorting
            } for row in gate_register
        ]
        
        # Sort options
        sort_by = request.args.get('sort_by', 'street_name')  # Default sort by street name
        sort_order = request.args.get('sort_order', 'asc')  # asc or desc
        
        if sort_by == 'street_name':
            register_data.sort(key=lambda x: (x['street_name'], int(x['street_number']) if x['street_number'].isdigit() else 999))
        elif sort_by == 'last_name':
            register_data.sort(key=lambda x: x['last_name'])
        elif sort_by == 'erf_number':
            register_data.sort(key=lambda x: x['erf_number'])
        
        if sort_order == 'desc':
            register_data.reverse()
        
        return jsonify({
            'register': register_data,
            'total_entries': len(register_data),
            'sorted_by': sort_by,
            'sort_order': sort_order
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Admin Vehicle Management Endpoints
@admin_bp.route('/residents/<user_id>/vehicles', methods=['GET'])
@jwt_required()
def get_resident_vehicles(user_id):
    """Get all vehicles for a specific user (admin access) - supports both residents and owners"""
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        user = User.query.get_or_404(user_id)
        
        vehicles = []
        
        # Get vehicles from resident data
        if user.resident:
            resident_vehicles = Vehicle.query.filter_by(resident_id=user.resident.id).all()
            vehicles.extend([vehicle.to_dict() for vehicle in resident_vehicles])
        
        # Get vehicles from owner data (for all users who have owner records)
        if user.owner:
            owner_vehicles = Vehicle.query.filter_by(owner_id=user.owner.id).all()
            vehicles.extend([vehicle.to_dict() for vehicle in owner_vehicles])
        
        return jsonify(vehicles), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/residents/<user_id>/vehicles', methods=['POST'])
@jwt_required()
def add_resident_vehicle(user_id):
    """Add a vehicle for a specific user (admin access) - supports both residents and owners"""
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        user = User.query.get_or_404(user_id)
        
        # Must be either a resident or owner
        if not user.resident and not user.owner:
            return jsonify({'error': 'User must be a resident or owner to have vehicles'}), 400
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('registration_number'):
            return jsonify({'error': 'Registration number is required'}), 400
        
        # Check if registration number already exists
        existing_vehicle = Vehicle.query.filter_by(registration_number=data['registration_number']).first()
        if existing_vehicle:
            return jsonify({'error': 'Vehicle with this registration number already exists'}), 400
        
        # Create new vehicle - prefer resident_id if available, otherwise use owner_id
        vehicle = Vehicle(
            resident_id=user.resident.id if user.resident else None,
            owner_id=user.owner.id if (user.owner and not user.resident) else None,
            registration_number=data['registration_number'],
            make=data.get('make', ''),
            model=data.get('model', ''),
            color=data.get('color', '')
        )
        
        db.session.add(vehicle)
        db.session.commit()
        
        # Log vehicle addition for admin change tracking
        try:
            # Get user display name and ERF number for logging
            if user.resident:
                user_name = f"{user.resident.first_name} {user.resident.last_name}".strip()
                erf_number = user.resident.erf_number or 'Unknown'
            elif user.owner:
                user_name = f"{user.owner.first_name} {user.owner.last_name}".strip()
                erf_number = user.owner.erf_number or 'Unknown'
            else:
                user_name = user.email
                erf_number = 'Unknown'
            
            # Log the new vehicle addition by admin
            log_user_change(
                user.id, 
                user_name, 
                erf_number, 
                'admin_add', 
                'vehicle_registration', 
                'None', 
                data['registration_number']
            )
            
            # Also log other vehicle details if provided
            if data.get('make'):
                log_user_change(user.id, user_name, erf_number, 'admin_add', 'vehicle_make', 'None', data['make'])
            
            if data.get('model'):
                log_user_change(user.id, user_name, erf_number, 'admin_add', 'vehicle_model', 'None', data['model'])
            
            if data.get('color'):
                log_user_change(user.id, user_name, erf_number, 'admin_add', 'vehicle_color', 'None', data['color'])
                
        except Exception as log_error:
            print(f"Error logging admin vehicle addition: {log_error}")
        
        return jsonify({
            'message': 'Vehicle added successfully',
            'vehicle': vehicle.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/residents/<user_id>/vehicles/<vehicle_id>', methods=['PUT'])
@jwt_required()
def update_resident_vehicle(user_id, vehicle_id):
    """Update a vehicle for a specific user (admin access) - supports both residents and owners"""
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        user = User.query.get_or_404(user_id)
        
        # Find vehicle belonging to this user (resident or owner)
        vehicle = None
        if user.resident:
            vehicle = Vehicle.query.filter_by(id=vehicle_id, resident_id=user.resident.id).first()
        if not vehicle and user.owner:
            vehicle = Vehicle.query.filter_by(id=vehicle_id, owner_id=user.owner.id).first()
        
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        data = request.get_json()
        
        # Check if new registration number conflicts with existing vehicles
        if data.get('registration_number') and data['registration_number'] != vehicle.registration_number:
            existing_vehicle = Vehicle.query.filter_by(registration_number=data['registration_number']).first()
            if existing_vehicle:
                return jsonify({'error': 'Vehicle with this registration number already exists'}), 400
        
        # Store old values for logging before updating
        old_registration = vehicle.registration_number
        old_make = vehicle.make
        old_model = vehicle.model
        old_color = vehicle.color
        
        # Update vehicle fields
        if 'registration_number' in data:
            vehicle.registration_number = data['registration_number']
        if 'make' in data:
            vehicle.make = data['make']
        if 'model' in data:
            vehicle.model = data['model']
        if 'color' in data:
            vehicle.color = data['color']

        # Log changes for admin change tracking
        try:
            # Get user display name and ERF number for logging
            if user.resident:
                user_name = f"{user.resident.first_name} {user.resident.last_name}".strip()
                erf_number = user.resident.erf_number or 'Unknown'
            elif user.owner:
                user_name = f"{user.owner.first_name} {user.owner.last_name}".strip()
                erf_number = user.owner.erf_number or 'Unknown'
            else:
                user_name = user.email
                erf_number = 'Unknown'
            
            # Log vehicle registration changes (critical field)
            if 'registration_number' in data and data['registration_number'] != old_registration:
                log_user_change(user.id, user_name, erf_number, 'admin_update', 'vehicle_registration', old_registration, data['registration_number'])
            
            # Log other vehicle changes
            if 'make' in data and data['make'] != old_make:
                log_user_change(user.id, user_name, erf_number, 'admin_update', 'vehicle_make', old_make, data['make'])
            
            if 'model' in data and data['model'] != old_model:
                log_user_change(user.id, user_name, erf_number, 'admin_update', 'vehicle_model', old_model, data['model'])
            
            if 'color' in data and data['color'] != old_color:
                log_user_change(user.id, user_name, erf_number, 'admin_update', 'vehicle_color', old_color, data['color'])
                
        except Exception as log_error:
            print(f"Error logging admin vehicle change: {log_error}")
        
        db.session.commit()
        
        return jsonify({
            'message': 'Vehicle updated successfully',
            'vehicle': vehicle.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/residents/<user_id>/vehicles/<vehicle_id>', methods=['DELETE'])
@jwt_required()
def delete_resident_vehicle(user_id, vehicle_id):
    """Delete a vehicle for a specific user (admin access) - supports both residents and owners"""
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        user = User.query.get_or_404(user_id)
        
        # Find vehicle belonging to this user (resident or owner)
        vehicle = None
        if user.resident:
            vehicle = Vehicle.query.filter_by(id=vehicle_id, resident_id=user.resident.id).first()
        if not vehicle and user.owner:
            vehicle = Vehicle.query.filter_by(id=vehicle_id, owner_id=user.owner.id).first()
        
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        db.session.delete(vehicle)
        db.session.commit()
        
        return jsonify({'message': 'Vehicle deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/system-status', methods=['GET'])
def get_system_status():
    """Health check endpoint for Render deployment"""
    try:
        # Quick database check
        user_count = User.query.count()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'users': user_count,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# ERF Address Mapping Routes
@admin_bp.route('/address-mappings', methods=['GET'])
@jwt_required()
def get_address_mappings():
    """Get all ERF address mappings"""
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        mappings = ErfAddressMapping.query.order_by(ErfAddressMapping.erf_number.cast(db.Integer)).all()
        return jsonify({
            'success': True,
            'data': [mapping.to_dict() for mapping in mappings],
            'count': len(mappings)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/address-mappings/upload', methods=['POST'])
@jwt_required()
def upload_address_mappings():
    """Upload and process ERF address mappings from CSV file"""
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith(('.csv', '.xlsx')):
            return jsonify({'error': 'File must be CSV or Excel format'}), 400
        
        current_user_id = get_jwt_identity()
        
        # Read file content
        try:
            if file.filename.lower().endswith('.csv'):
                # Read CSV file
                content = file.read().decode('utf-8')
                df = pd.read_csv(io.StringIO(content))
            else:
                # Read Excel file
                df = pd.read_excel(file)
        except Exception as e:
            return jsonify({'error': f'Failed to read file: {str(e)}'}), 400
        
        # Validate required columns
        required_columns = ['erf_number', 'street_number', 'street_name']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return jsonify({
                'error': f'Missing required columns: {", ".join(missing_columns)}',
                'required_columns': required_columns,
                'found_columns': list(df.columns)
            }), 400
        
        # Process and validate data
        address_data = []
        errors = []
        
        for index, row in df.iterrows():
            try:
                erf_number = str(row['erf_number']).strip()
                street_number = str(row['street_number']).strip()
                street_name = str(row['street_name']).strip()
                
                # Validate required fields
                if not erf_number or erf_number.lower() in ['nan', 'none', '']:
                    errors.append(f"Row {index + 2}: ERF number is required")
                    continue
                
                if not street_number or street_number.lower() in ['nan', 'none', '']:
                    errors.append(f"Row {index + 2}: Street number is required")
                    continue
                
                if not street_name or street_name.lower() in ['nan', 'none', '']:
                    errors.append(f"Row {index + 2}: Street name is required")
                    continue
                
                # Create full address
                full_address = f"{street_number} {street_name}"
                
                # Optional fields
                suburb = str(row.get('suburb', '')).strip() if 'suburb' in row and pd.notna(row.get('suburb')) else ''
                postal_code = str(row.get('postal_code', '')).strip() if 'postal_code' in row and pd.notna(row.get('postal_code')) else ''
                
                if suburb:
                    full_address += f", {suburb}"
                if postal_code:
                    full_address += f", {postal_code}"
                
                address_data.append({
                    'erf_number': erf_number,
                    'street_number': street_number,
                    'street_name': street_name,
                    'full_address': full_address,
                    'suburb': suburb,
                    'postal_code': postal_code
                })
                
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
        
        if errors:
            return jsonify({
                'error': 'Data validation failed',
                'errors': errors[:10],  # Limit to first 10 errors
                'total_errors': len(errors)
            }), 400
        
        if not address_data:
            return jsonify({'error': 'No valid data found in file'}), 400
        
        # Import data
        success, message = ErfAddressMapping.bulk_import_addresses(address_data, current_user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'imported_count': len(address_data)
            }), 200
        else:
            return jsonify({'error': message}), 500
            
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@admin_bp.route('/address-mappings/lookup/<erf_number>', methods=['GET'])
@jwt_required()
def lookup_address_by_erf(erf_number):
    """Get address details for a specific ERF number"""
    try:
        address_data = ErfAddressMapping.get_address_by_erf(erf_number)
        
        if address_data:
            return jsonify({
                'success': True,
                'data': address_data
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'No address found for ERF {erf_number}'
            }), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/address-mappings/template', methods=['GET'])
@jwt_required()
def download_address_template():
    """Download CSV template for address mappings"""
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        # Create CSV template
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'erf_number',
            'street_number', 
            'street_name',
            'suburb',
            'postal_code'
        ])
        
        # Write sample data
        writer.writerow([
            '12345',
            '123',
            'Main Street',
            'Altona Village',
            '0001'
        ])
        writer.writerow([
            '12346',
            '125',
            'Main Street',
            'Altona Village',
            '0001'
        ])
        writer.writerow([
            '12347',
            '1',
            'Oak Avenue',
            'Altona Village',
            '0001'
        ])
        
        # Generate response
        output.seek(0)
        csv_content = output.getvalue()
        output.close()
        
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': 'attachment; filename=erf_address_template.csv',
                'Content-Type': 'text/csv; charset=utf-8'
            }
        )
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate template: {str(e)}'}), 500

@admin_bp.route('/address-mappings/<int:mapping_id>', methods=['DELETE'])
@jwt_required()
def delete_address_mapping(mapping_id):
    """Delete a specific address mapping"""
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        mapping = ErfAddressMapping.query.get(mapping_id)
        if not mapping:
            return jsonify({'error': 'Address mapping not found'}), 404
        
        db.session.delete(mapping)
        db.session.commit()
        
        return jsonify({'message': 'Address mapping deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/address-mappings/clear', methods=['DELETE'])
@jwt_required()
def clear_all_address_mappings():
    """Clear all address mappings"""
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        count = ErfAddressMapping.query.count()
        ErfAddressMapping.query.delete()
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully cleared {count} address mappings'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

