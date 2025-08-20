from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import User, Resident, Owner, db
from src.models.user import UserTransitionRequest
from datetime import datetime

transition_linking_bp = Blueprint('transition_linking', __name__)

def admin_required():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    return None

@transition_linking_bp.route('/admin/link-existing-requests', methods=['POST'])
@jwt_required()
def link_existing_transition_requests():
    """Link two existing transition requests for the same ERF (owner and tenant), process migration, and update statuses."""
    admin_check = admin_required()
    if admin_check:
        return admin_check

    data = request.get_json()
    owner_request_id = data.get('owner_request_id')
    tenant_request_id = data.get('tenant_request_id')

    if not owner_request_id or not tenant_request_id:
        return jsonify({'error': 'Both request IDs are required'}), 400

    owner_request = UserTransitionRequest.query.get(owner_request_id)
    tenant_request = UserTransitionRequest.query.get(tenant_request_id)

    if not owner_request or not tenant_request:
        return jsonify({'error': 'One or both transition requests not found'}), 404

    # Check both requests are for the same ERF and not completed
    if owner_request.erf_number != tenant_request.erf_number:
        return jsonify({'error': 'Transition requests are for different ERFs'}), 400
    if owner_request.status == 'completed' or tenant_request.status == 'completed':
        return jsonify({'error': 'One or both transition requests are already completed'}), 400

    # Check roles
    owner_user = User.query.get(owner_request.user_id)
    tenant_user = User.query.get(tenant_request.user_id)
    if not owner_user or not tenant_user:
        return jsonify({'error': 'One or both users not found'}), 404

    # Owner must be owner, tenant must be resident/tenant
    owner_is_owner = Owner.query.filter_by(user_id=owner_user.id, erf_number=owner_request.erf_number).first() is not None
    tenant_is_resident = Resident.query.filter_by(user_id=tenant_user.id, erf_number=tenant_request.erf_number).first() is not None
    if not owner_is_owner or not tenant_is_resident:
        return jsonify({'error': 'Role mismatch: owner/tenant records not found for ERF'}), 400

    # Process migration: make tenant the new owner-resident, deactivate seller
    try:
        # Deactivate seller (owner)
        owner_user.status = 'inactive'
        owner_request.status = 'completed'
        owner_request.completed_at = datetime.utcnow()

        # Update tenant to owner-resident
        tenant_user.role = 'owner-resident'
        tenant_request.status = 'completed'
        tenant_request.completed_at = datetime.utcnow()

        # Update Resident and Owner tables
        # Remove old owner record
        Owner.query.filter_by(user_id=owner_user.id, erf_number=owner_request.erf_number).delete()
        # Add new owner record for tenant
        new_owner = Owner(user_id=tenant_user.id, erf_number=tenant_request.erf_number, first_name=tenant_user.first_name, last_name=tenant_user.last_name, phone_number=tenant_user.phone_number)
        db.session.add(new_owner)

        # Optionally update Resident record for tenant (set is_owner=True)
        resident_record = Resident.query.filter_by(user_id=tenant_user.id, erf_number=tenant_request.erf_number).first()
        if resident_record:
            resident_record.is_owner = True

        db.session.commit()
        return jsonify({'success': True, 'message': 'Transition requests linked and migration processed.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to process migration: {str(e)}'}), 500
