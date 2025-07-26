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
        required_fields = ['email', 'password', 'first_name', 'last_name', 'is_owner']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create user
        user = User(
            email=data['email'],
            role='resident',
            status='pending'
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.flush()  # Get the user ID
        
        # Create resident profile
        resident = Resident(
            user_id=user.id,
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone_number=data.get('phone_number'),
            emergency_contact_name=data.get('emergency_contact_name'),
            emergency_contact_number=data.get('emergency_contact_number'),
            is_owner=data['is_owner']
        )
        
        db.session.add(resident)
        db.session.commit()
        
        return jsonify({
            'message': 'Registration successful. Awaiting admin approval.',
            'user_id': user.id
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

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        profile_data = user.to_dict()
        
        if user.resident:
            profile_data['resident'] = user.resident.to_dict()
        
        return jsonify(profile_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update resident information
        if user.resident:
            resident = user.resident
            resident.first_name = data.get('first_name', resident.first_name)
            resident.last_name = data.get('last_name', resident.last_name)
            resident.phone_number = data.get('phone_number', resident.phone_number)
            resident.emergency_contact_name = data.get('emergency_contact_name', resident.emergency_contact_name)
            resident.emergency_contact_number = data.get('emergency_contact_number', resident.emergency_contact_number)
        
        db.session.commit()
        
        return jsonify({'message': 'Profile updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

