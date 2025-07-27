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
            
            if 'property_address' in data:
                # Parse the address and update components
                from src.routes.auth import parse_address
                street_number, street_name = parse_address(data['property_address'])
                owner.street_number = street_number
                owner.street_name = street_name
                owner.full_address = data['property_address']
        
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
    print(f'=== COMPLAINT UPDATE BACKEND DEBUG ===')
    print(f'Complaint ID received: {complaint_id}')
    print(f'Complaint ID type: {type(complaint_id)}')
    print(f'Request data: {request.get_json()}')
    
    admin_check = admin_required()
    if admin_check:
        print('Admin check failed')
        return admin_check
    
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        print(f'User ID: {user_id}')
        print(f'Request data parsed: {data}')
        
        complaint = Complaint.query.get(complaint_id)
        print(f'Complaint found: {complaint}')
        if not complaint:
            print('Complaint not found in database')
            return jsonify({'error': 'Complaint not found'}), 404
        
        print(f'Current complaint status: {complaint.status}')
        
        # Update complaint status if provided
        if 'status' in data:
            print(f'Updating status from {complaint.status} to {data["status"]}')
            complaint.status = data['status']
        
        if 'priority' in data:
            print(f'Updating priority to {data["priority"]}')
            complaint.priority = data['priority']
        
        if 'assigned_to' in data:
            print(f'Updating assigned_to to {data["assigned_to"]}')
            complaint.assigned_to = data['assigned_to']
        
        # Add update if provided
        if 'update_text' in data:
            print(f'Adding update text: {data["update_text"]}')
            update = ComplaintUpdate(
                complaint_id=complaint_id,
                user_id=user_id,
                update_text=data['update_text']
            )
            db.session.add(update)
        
        print('Committing changes to database')
        db.session.commit()
        print('Changes committed successfully')
        
        return jsonify({'message': 'Complaint updated successfully'}), 200
        
    except Exception as e:
        print(f'Exception occurred: {str(e)}')
        print(f'Exception type: {type(e)}')
        import traceback
        traceback.print_exc()
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

