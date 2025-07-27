from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from src.models.user import User, Resident, Owner, db
from src.utils.email_service import send_registration_notification_to_admin
from datetime import timedelta

def parse_address(address):
    """Parse address to extract street number and street name"""
    if not address:
        return "", ""
    
    # Remove common suffixes that shouldn't be in the basic address
    address = address.replace("Altona Village", "").replace("Worcester", "").strip()
    
    # Try to find number at the beginning
    parts = address.split()
    street_number = ""
    street_name = ""
    
    if parts:
        # Check if first part is a number
        if parts[0].isdigit():
            street_number = parts[0]
            street_name = " ".join(parts[1:]).strip()
        else:
            # Check if last part is a number
            if parts[-1].isdigit():
                street_number = parts[-1]
                street_name = " ".join(parts[:-1]).strip()
            else:
                # Look for number in middle or extract first number found
                for i, part in enumerate(parts):
                    if part.isdigit():
                        street_number = part
                        street_name = " ".join(parts[:i] + parts[i+1:]).strip()
                        break
                
                # If no number found, use entire address as street name
                if not street_number:
                    street_name = address
    
    return street_number or "", street_name or address

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = [
            'email', 'password', 'first_name', 'last_name', 'id_number',
            'erf_number', 'is_owner', 'is_resident'
        ]
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate address fields - either combined address OR separate components
        if not (data.get('address') or (data.get('street_number') and data.get('street_name'))):
            return jsonify({'error': 'Address information is required (either address or street_number + street_name)'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create user
        user = User(
            email=data['email'],
            role='pending',  # or 'resident' if you want
            status='pending'
        )
        user.set_password(data['password'])
        db.session.add(user)
        db.session.flush()  # Get the user ID

        # Create Resident if checked
        if data['is_resident']:
            # Handle separate address components or parse combined address
            if 'street_number' in data and 'street_name' in data:
                # Use separate fields if provided
                street_number = data['street_number']
                street_name = data['street_name']
                full_address = f"{street_number} {street_name}".strip()
            else:
                # Parse combined address for backward compatibility
                street_number, street_name = parse_address(data['address'])
                full_address = data['address']
            
            resident = Resident(
                user_id=user.id,
                first_name=data['first_name'],
                last_name=data['last_name'],
                phone_number=data.get('phone_number'),
                emergency_contact_name=data.get('emergency_contact_name'),
                emergency_contact_number=data.get('emergency_contact_number'),
                id_number=data['id_number'],
                erf_number=data['erf_number'],
                street_number=street_number,
                street_name=street_name,
                full_address=full_address
            )
            db.session.add(resident)

        # Create Owner if checked
        if data['is_owner']:
            # Handle separate address components or parse combined address
            if 'street_number' in data and 'street_name' in data:
                # Use separate fields if provided
                street_number = data['street_number']
                street_name = data['street_name']
                full_address = f"{street_number} {street_name}".strip()
            else:
                # Parse combined address for backward compatibility
                street_number, street_name = parse_address(data['address'])
                full_address = data['address']
            
            owner = Owner(
                user_id=user.id,
                first_name=data['first_name'],
                last_name=data['last_name'],
                phone_number=data.get('phone_number'),
                emergency_contact_name=data.get('emergency_contact_name'),
                emergency_contact_number=data.get('emergency_contact_number'),
                id_number=data['id_number'],
                erf_number=data['erf_number'],
                street_number=street_number,
                street_name=street_name,
                full_address=full_address,
                full_postal_address=data.get('postal_address'),
                title_deed_number=data.get('title_deed_number')
            )
            db.session.add(owner)

        db.session.commit()
        
        # Send notification email to admin about new registration
        try:
            send_registration_notification_to_admin(
                user.email, 
                data['first_name'], 
                data['last_name']
            )
        except Exception as email_error:
            print(f"Admin notification email failed: {email_error}")
            # Don't fail registration if email fails
        
        return jsonify({
            'message': 'Registration successful. Your application is pending admin approval. You will receive an email notification once approved.',
            'user_id': user.id,
            'status': 'pending'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400

        user = User.query.filter_by(email=data['email']).first()
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid email or password'}), 401

        if user.status != 'active':
            if user.status == 'pending':
                return jsonify({'error': 'Your account is still pending admin approval. You will receive an email notification once approved.'}), 401
            else:
                return jsonify({'error': 'Account not activated. Please contact admin.'}), 401

        # Create access token
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(days=7)
        )

        return jsonify({
            'access_token': access_token,
            'user': user.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Add this route at the end of the file ---

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Create profile data in the format frontend expects
    profile_data = {
        'id': user.id,
        'email': user.email,
        'role': user.role,
        'status': user.status,
        'full_name': user.get_full_name() or '',
        'phone': '',
        'property_address': '',
        'tenant_or_owner': '',
        'emergency_contact_name': '',
        'emergency_contact_phone': ''
    }
    
    # Add resident data if available
    if user.resident:
        resident = user.resident
        profile_data.update({
            'phone': resident.phone_number or '',
            'property_address': resident.full_address or '',
            'emergency_contact_name': resident.emergency_contact_name or '',
            'emergency_contact_phone': resident.emergency_contact_number or ''
        })
    
    # Add owner data if available (overrides resident data for shared fields)
    if user.owner:
        owner = user.owner
        profile_data.update({
            'phone': owner.phone_number or profile_data['phone'],
            'property_address': owner.full_address or profile_data['property_address'],
            'emergency_contact_name': owner.emergency_contact_name or profile_data['emergency_contact_name'],
            'emergency_contact_phone': owner.emergency_contact_number or profile_data['emergency_contact_phone']
        })
    
    # Determine tenant_or_owner status
    if user.is_owner() and user.is_resident():
        profile_data['tenant_or_owner'] = 'owner'  # Owner-resident defaults to owner
    elif user.is_owner():
        profile_data['tenant_or_owner'] = 'owner'
    elif user.is_resident():
        profile_data['tenant_or_owner'] = 'tenant'
    
    print(f"[DEBUG] GET profile returning: {profile_data}")
    return jsonify(profile_data), 200

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile information"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            print(f"[DEBUG] User not found: {user_id}")
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        print(f"[DEBUG] Received profile update data: {data}")
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        # Update User model fields
        if 'email' in data:
            # Check if email is already taken by another user
            existing_user = User.query.filter(User.email == data['email'], User.id != user_id).first()
            if existing_user:
                return jsonify({'error': 'Email already in use'}), 400
            user.email = data['email']
        
        # Update password if provided
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        # Handle full_name field from frontend - split into first and last name
        if 'full_name' in data and data['full_name']:
            name_parts = data['full_name'].strip().split(' ', 1)
            data['first_name'] = name_parts[0]
            data['last_name'] = name_parts[1] if len(name_parts) > 1 else ''
        
        # Map frontend field names to backend field names
        if 'phone' in data:
            data['phone_number'] = data['phone']
        if 'property_address' in data:
            data['full_address'] = data['property_address']
        if 'emergency_contact_phone' in data:
            data['emergency_contact_number'] = data['emergency_contact_phone']
        
        # Update Resident information if user is a resident
        if user.resident and any(field in data for field in [
            'first_name', 'last_name', 'phone_number', 'id_number', 
            'street_number', 'street_name', 'erf_number', 
            'emergency_contact_name', 'emergency_contact_number'
        ]):
            resident = user.resident
            
            # Update basic info
            if 'first_name' in data:
                resident.first_name = data['first_name']
            if 'last_name' in data:
                resident.last_name = data['last_name']
            if 'phone_number' in data:
                resident.phone_number = data['phone_number']
            if 'id_number' in data:
                resident.id_number = data['id_number']
            if 'erf_number' in data:
                resident.erf_number = data['erf_number']
            
            # Update address components
            if 'street_number' in data:
                resident.street_number = data['street_number']
            if 'street_name' in data:
                resident.street_name = data['street_name']
            
            # Update full address if street components are provided
            if 'street_number' in data or 'street_name' in data:
                street_num = data.get('street_number', resident.street_number)
                street_name = data.get('street_name', resident.street_name)
                resident.full_address = f"{street_num} {street_name}".strip()
            elif 'full_address' in data:
                resident.full_address = data['full_address']
            
            # Update emergency contacts
            if 'emergency_contact_name' in data:
                resident.emergency_contact_name = data['emergency_contact_name']
            if 'emergency_contact_number' in data:
                resident.emergency_contact_number = data['emergency_contact_number']
            
            # Update timestamps
            from datetime import datetime
            resident.updated_at = datetime.utcnow()
        
        # Update Owner information if user is an owner
        if user.owner and any(field in data for field in [
            'first_name', 'last_name', 'phone_number', 'id_number',
            'street_number', 'street_name', 'erf_number', 'title_deed_number',
            'postal_street_number', 'postal_street_name', 'postal_suburb',
            'postal_city', 'postal_code', 'postal_province',
            'emergency_contact_name', 'emergency_contact_number'
        ]):
            owner = user.owner
            
            # Update basic info
            if 'first_name' in data:
                owner.first_name = data['first_name']
            if 'last_name' in data:
                owner.last_name = data['last_name']
            if 'phone_number' in data:
                owner.phone_number = data['phone_number']
            if 'id_number' in data:
                owner.id_number = data['id_number']
            if 'erf_number' in data:
                owner.erf_number = data['erf_number']
            if 'title_deed_number' in data:
                owner.title_deed_number = data['title_deed_number']
            
            # Update address components
            if 'street_number' in data:
                owner.street_number = data['street_number']
            if 'street_name' in data:
                owner.street_name = data['street_name']
            
            # Update full address if street components are provided
            if 'street_number' in data or 'street_name' in data:
                street_num = data.get('street_number', owner.street_number)
                street_name = data.get('street_name', owner.street_name)
                owner.full_address = f"{street_num} {street_name}".strip()
            elif 'full_address' in data:
                owner.full_address = data['full_address']
            
            # Update postal address components
            if 'postal_street_number' in data:
                owner.postal_street_number = data['postal_street_number']
            if 'postal_street_name' in data:
                owner.postal_street_name = data['postal_street_name'] 
            if 'postal_suburb' in data:
                owner.postal_suburb = data['postal_suburb']
            if 'postal_city' in data:
                owner.postal_city = data['postal_city']
            if 'postal_code' in data:
                owner.postal_code = data['postal_code']
            if 'postal_province' in data:
                owner.postal_province = data['postal_province']
            
            # Update full postal address if components are provided
            postal_parts = []
            if owner.postal_street_number and owner.postal_street_name:
                postal_parts.append(f"{owner.postal_street_number} {owner.postal_street_name}")
            if owner.postal_suburb:
                postal_parts.append(owner.postal_suburb)
            if owner.postal_city:
                postal_parts.append(owner.postal_city)
            if owner.postal_code:
                postal_parts.append(owner.postal_code)
            if owner.postal_province:
                postal_parts.append(owner.postal_province)
            
            if postal_parts:
                owner.full_postal_address = ", ".join(postal_parts)
            elif 'full_postal_address' in data:
                owner.full_postal_address = data['full_postal_address']
            
            # Update emergency contacts
            if 'emergency_contact_name' in data:
                owner.emergency_contact_name = data['emergency_contact_name']
            if 'emergency_contact_number' in data:
                owner.emergency_contact_number = data['emergency_contact_number']
            
            # Update timestamps
            from datetime import datetime
            owner.updated_at = datetime.utcnow()
        
        # Update user timestamp
        from datetime import datetime
        user.updated_at = datetime.utcnow()
        
        # Commit all changes
        db.session.commit()
        
        response_data = {
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }
        print(f"[DEBUG] Sending response: {response_data}")
        return jsonify(response_data), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Profile update error: {str(e)}")  # For debugging
        return jsonify({'error': f'Failed to update profile: {str(e)}'}), 500