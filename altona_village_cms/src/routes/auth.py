from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from src.models.user import User, Resident, db
from datetime import timedelta

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = [
            'email', 'password', 'first_name', 'last_name', 'id_number',
            'erf_number', 'address', 'is_owner', 'is_resident'
        ]
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
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
            resident = Resident(
                user_id=user.id,
                first_name=data['first_name'],
                last_name=data['last_name'],
                phone_number=data.get('phone_number'),
                emergency_contact_name=data.get('emergency_contact_name'),
                emergency_contact_number=data.get('emergency_contact_number'),
                id_number=data['id_number'],
                erf_number=data['erf_number'],
                address=data['address'],
                is_owner=data['is_owner']
            )
            db.session.add(resident)

        # Create Owner if checked (if you have an Owner model)
        if data['is_owner']:
            # Uncomment and adjust if you have an Owner model
            # owner = Owner(
            #     user_id=user.id,
            #     first_name=data['first_name'],
            #     last_name=data['last_name'],
            #     id_number=data['id_number'],
            #     erf_number=data['erf_number'],
            #     address=data['address'],
            #     phone_number=data.get('phone_number'),
            #     email=data['email']
            # )
            # db.session.add(owner)
            pass  # Remove this if you add the Owner logic above

        db.session.commit()
        
        return jsonify({
            'message': 'Registration successful. Awaiting admin approval.',
            'user_id': user.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500