from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from src.models.user import User, Resident, db
from src.utils.email_service import send_registration_notification_to_admin
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
    return jsonify(user.to_dict()), 200