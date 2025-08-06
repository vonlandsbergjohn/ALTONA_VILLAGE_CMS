from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from ..models.user import db, User, Resident, Owner, Vehicle
from sqlalchemy import or_, and_

user_management_bp = Blueprint('user_management', __name__)

@user_management_bp.route('/admin/users/inactive', methods=['GET'])
@jwt_required()
def get_inactive_users():
    """Get all inactive users (not archived yet)"""
    try:
        current_user = User.query.get(get_jwt_identity())
        
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        # Get all inactive users that are not archived
        inactive_users = User.query.filter(
            and_(
                User.status == 'inactive',
                or_(User.archived == False, User.archived.is_(None))
            )
        ).all()
        
        users_data = []
        for user in inactive_users:
            user_data = user.to_dict()
            
            # Add ERF information
            erfs = []
            if user.resident:
                erfs.append({
                    'erf_number': user.resident.erf_number,
                    'type': 'resident',
                    'migration_date': user.resident.migration_date.isoformat() if user.resident.migration_date else None,
                    'migration_reason': user.resident.migration_reason
                })
            if user.owner:
                erfs.append({
                    'erf_number': user.owner.erf_number,
                    'type': 'owner',
                    'migration_date': user.owner.migration_date.isoformat() if user.owner.migration_date else None,
                    'migration_reason': user.owner.migration_reason
                })
            
            user_data['erfs'] = erfs
            users_data.append(user_data)
        
        return jsonify({
            'users': users_data,
            'total': len(users_data)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching inactive users: {str(e)}")
        return jsonify({'error': 'Failed to fetch inactive users'}), 500

@user_management_bp.route('/admin/users/archived', methods=['GET'])
@jwt_required()
def get_archived_users():
    """Get all archived users"""
    try:
        current_user = User.query.get(get_jwt_identity())
        
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        # Get all archived users
        archived_users = User.query.filter(User.archived == True).all()
        
        users_data = []
        for user in archived_users:
            user_data = user.to_dict()
            
            # Add ERF information
            erfs = []
            if user.resident:
                erfs.append({
                    'erf_number': user.resident.erf_number,
                    'type': 'resident',
                    'migration_date': user.resident.migration_date.isoformat() if user.resident.migration_date else None,
                    'migration_reason': user.resident.migration_reason
                })
            if user.owner:
                erfs.append({
                    'erf_number': user.owner.erf_number,
                    'type': 'owner',
                    'migration_date': user.owner.migration_date.isoformat() if user.owner.migration_date else None,
                    'migration_reason': user.owner.migration_reason
                })
            
            # Add archived by user info
            if user.archived_by:
                archived_by_user = User.query.get(user.archived_by)
                if archived_by_user:
                    user_data['archived_by_user'] = archived_by_user.get_full_name()
                else:
                    user_data['archived_by_user'] = 'Unknown'
            
            user_data['erfs'] = erfs
            users_data.append(user_data)
        
        return jsonify({
            'users': users_data,
            'total': len(users_data)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching archived users: {str(e)}")
        return jsonify({'error': 'Failed to fetch archived users'}), 500

@user_management_bp.route('/admin/users/<user_id>/archive', methods=['POST'])
@jwt_required()
def archive_user(user_id):
    """Archive an inactive user"""
    try:
        current_user = User.query.get(get_jwt_identity())
        
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        user = User.query.get_or_404(user_id)
        
        # Can only archive inactive users
        if user.status != 'inactive':
            return jsonify({'error': 'Can only archive inactive users'}), 400
        
        # Check if already archived
        if user.archived:
            return jsonify({'error': 'User is already archived'}), 400
        
        data = request.get_json()
        archive_reason = data.get('reason', 'Archived by admin')
        
        # Archive the user
        user.archived = True
        user.archived_at = datetime.utcnow()
        user.archived_by = current_user.id
        user.archive_reason = archive_reason
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': f'User {user.get_full_name()} archived successfully',
            'user_id': user_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error archiving user: {str(e)}")
        return jsonify({'error': 'Failed to archive user'}), 500

@user_management_bp.route('/admin/users/<user_id>/unarchive', methods=['POST'])
@jwt_required()
def unarchive_user(user_id):
    """Unarchive a user (restore to inactive status)"""
    try:
        current_user = User.query.get(get_jwt_identity())
        
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        user = User.query.get_or_404(user_id)
        
        # Can only unarchive archived users
        if not user.archived:
            return jsonify({'error': 'User is not archived'}), 400
        
        # Unarchive the user (restore to inactive status)
        user.archived = False
        user.archived_at = None
        user.archived_by = None
        user.archive_reason = None
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': f'User {user.get_full_name()} unarchived successfully',
            'user_id': user_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error unarchiving user: {str(e)}")
        return jsonify({'error': 'Failed to unarchive user'}), 500

@user_management_bp.route('/admin/users/<user_id>/delete', methods=['DELETE'])
@jwt_required()
def permanently_delete_user(user_id):
    """Permanently delete an archived user and all related data"""
    try:
        current_user = User.query.get(get_jwt_identity())
        
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        user = User.query.get_or_404(user_id)
        
        # Can only permanently delete archived users
        if not user.archived:
            return jsonify({'error': 'User must be archived before permanent deletion'}), 400
        
        data = request.get_json()
        confirm_deletion = data.get('confirm', False)
        
        if not confirm_deletion:
            return jsonify({'error': 'Deletion confirmation required'}), 400
        
        user_name = user.get_full_name()
        user_email = user.email
        
        # Get all related data before deletion
        erfs = []
        if user.resident:
            erfs.append(f"Resident ERF {user.resident.erf_number}")
        if user.owner:
            erfs.append(f"Owner ERF {user.owner.erf_number}")
        
        # Delete related vehicles first
        if user.resident:
            vehicles = Vehicle.query.filter_by(resident_id=user.resident.id).all()
            for vehicle in vehicles:
                db.session.delete(vehicle)
        
        if user.owner:
            vehicles = Vehicle.query.filter_by(owner_id=user.owner.id).all()
            for vehicle in vehicles:
                db.session.delete(vehicle)
        
        # The cascade delete should handle resident and owner records
        # when we delete the user
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'message': f'User {user_name} ({user_email}) permanently deleted',
            'deleted_user': {
                'name': user_name,
                'email': user_email,
                'erfs': erfs
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error permanently deleting user: {str(e)}")
        return jsonify({'error': 'Failed to permanently delete user'}), 500

@user_management_bp.route('/admin/users/archive-old', methods=['POST'])
@jwt_required()
def archive_old_inactive_users():
    """Archive all inactive users older than specified days"""
    try:
        current_user = User.query.get(get_jwt_identity())
        
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        days_threshold = data.get('days', 30)  # Default to 30 days
        archive_reason = data.get('reason', f'Auto-archived: inactive for {days_threshold}+ days')
        
        # Calculate the cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
        
        # Find inactive users that haven't been updated since cutoff date
        old_inactive_users = User.query.filter(
            and_(
                User.status == 'inactive',
                or_(User.archived == False, User.archived.is_(None)),
                User.updated_at < cutoff_date
            )
        ).all()
        
        archived_count = 0
        archived_users = []
        
        for user in old_inactive_users:
            user.archived = True
            user.archived_at = datetime.utcnow()
            user.archived_by = current_user.id
            user.archive_reason = archive_reason
            user.updated_at = datetime.utcnow()
            
            archived_users.append({
                'id': user.id,
                'name': user.get_full_name(),
                'email': user.email,
                'inactive_since': user.updated_at.isoformat() if user.updated_at else None
            })
            archived_count += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'Archived {archived_count} inactive users',
            'archived_users': archived_users,
            'days_threshold': days_threshold
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error archiving old inactive users: {str(e)}")
        return jsonify({'error': 'Failed to archive old users'}), 500
