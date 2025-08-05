from flask import Blueprint, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User, Resident, Owner, Vehicle
from datetime import datetime
import csv
import io

gate_register_bp = Blueprint('gate_register', __name__)

@gate_register_bp.route('/gate-register-legacy', methods=['GET'])
@jwt_required()
def get_gate_register():
    """
    Generate gate register for security guards
    Returns all residents (including owner-residents) sorted by street name
    Format: RESIDENT STATUS, SURNAME, STREET NR, STREET NAME, VEHICLE REGISTRATION NR, ERF NR, INTERCOM NR
    """
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Only admins can access gate register
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized access'}), 403
    
    try:
        # Get all active users with active status
        # Also include users who might be in transition states
        active_users = User.query.filter(User.status.in_(['active', 'approved'])).all()
        
        gate_entries = []
        
        for user in active_users:
            # Skip admin users
            if user.role == 'admin':
                continue
            
            # Determine resident status and get relevant data
            resident_data = None
            owner_data = None
            status = 'Unknown'
            
            if user.is_resident() and user.is_owner():
                status = 'Owner-Resident'
                resident_data = user.resident
                owner_data = user.owner
            elif user.is_resident():
                status = 'Resident'
                resident_data = user.resident
            elif user.is_owner():
                status = 'Owner'
                owner_data = user.owner
            
            # Get primary data source (residents get priority for intercom codes)
            primary_data = resident_data if resident_data else owner_data
            
            if not primary_data:
                continue  # Skip if no resident or owner data
            
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
                # Owners also need vehicles for property visits
                vehicles = Vehicle.query.filter_by(owner_id=owner_data.id).all()
                vehicle_registrations = [v.registration_number for v in vehicles]
            
            # Create entry for gate register
            entry = {
                'resident_status': status,
                'surname': primary_data.last_name or '',
                'first_name': primary_data.first_name or '',
                'street_number': primary_data.street_number or '',
                'street_name': primary_data.street_name or '',
                'vehicle_registrations': vehicle_registrations,
                'erf_number': primary_data.erf_number or '',
                # All status groups can have intercom codes - show if available
                'intercom_code': primary_data.intercom_code or '',
                'sort_key': (primary_data.street_name or '').upper()  # For sorting
            }
            
            gate_entries.append(entry)
        
        # Sort by street name alphabetically
        gate_entries.sort(key=lambda x: x['sort_key'])
        
        return jsonify({
            'success': True,
            'data': gate_entries,
            'total_entries': len(gate_entries),
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate gate register: {str(e)}'}), 500

@gate_register_bp.route('/gate-register/export', methods=['GET'])
@jwt_required()
def export_gate_register_csv():
    """
    Export gate register as CSV file for printing
    """
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Only admins can export gate register
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized access'}), 403
    
    try:
        # Get gate register data (reuse logic from above)
        # Also include users who might be in transition states
        active_users = User.query.filter(User.status.in_(['active', 'approved'])).all()
        gate_entries = []
        
        for user in active_users:
            if user.role == 'admin':
                continue
            
            resident_data = None
            owner_data = None
            status = 'Unknown'
            
            if user.is_resident() and user.is_owner():
                status = 'Owner-Resident'
                resident_data = user.resident
                owner_data = user.owner
            elif user.is_resident():
                status = 'Resident'
                resident_data = user.resident
            elif user.is_owner():
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
            
            # Get vehicle registrations
            vehicle_registrations = []
            if resident_data:
                vehicles = Vehicle.query.filter_by(resident_id=resident_data.id).all()
                vehicle_registrations = [v.registration_number for v in vehicles]
            elif owner_data:
                # Owners also need vehicles for property visits
                vehicles = Vehicle.query.filter_by(owner_id=owner_data.id).all()
                vehicle_registrations = [v.registration_number for v in vehicles]
            
            # Handle multiple vehicles - create separate row for each vehicle
            if vehicle_registrations:
                for vehicle_reg in vehicle_registrations:
                    entry = {
                        'resident_status': status,
                        'surname': primary_data.last_name or '',
                        'street_number': primary_data.street_number or '',
                        'street_name': primary_data.street_name or '',
                        'vehicle_registration': vehicle_reg,
                        'erf_number': primary_data.erf_number or '',
                        # All status groups can have intercom codes - show if available
                        'intercom_code': primary_data.intercom_code or '',
                        'sort_key': (primary_data.street_name or '').upper()
                    }
                    gate_entries.append(entry)
            else:
                # No vehicles - still include the resident/owner
                entry = {
                    'resident_status': status,
                    'surname': primary_data.last_name or '',
                    'street_number': primary_data.street_number or '',
                    'street_name': primary_data.street_name or '',
                    'vehicle_registration': '',
                    'erf_number': primary_data.erf_number or '',
                    # All status groups can have intercom codes - show if available
                    'intercom_code': primary_data.intercom_code or '',
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
