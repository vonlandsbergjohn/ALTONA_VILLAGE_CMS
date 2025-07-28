from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import text
from src.models.user import User, Resident, Owner, Property, Vehicle, Builder, Meter, Complaint, ComplaintUpdate, db
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
        active_users = User.query.filter_by(status='active').all()
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
                status = 'Non-Resident Owner'
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
        
        return jsonify({
            'success': True,
            'data': result,
            'count': len(result)
        }), 200
        
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
                'type': 'Owner-Resident' if user.is_owner_resident() else 'Non-Resident Owner',
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
                'type': 'Non-Resident Owner',
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
        
        # Update vehicle fields
        if 'registration_number' in data:
            vehicle.registration_number = data['registration_number']
        if 'make' in data:
            vehicle.make = data['make']
        if 'model' in data:
            vehicle.model = data['model']
        if 'color' in data:
            vehicle.color = data['color']
        
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

