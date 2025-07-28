# Admin Notifications Route - Track Critical User Updates
# For managing changes to cellphone numbers and vehicle registrations

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
from functools import wraps
import sqlite3
import os

admin_notifications = Blueprint('admin_notifications', __name__)

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'app.db')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First check if JWT is valid
        try:
            from flask_jwt_extended import verify_jwt_in_request
            verify_jwt_in_request()
        except:
            return jsonify({'error': 'Authentication required'}), 401
            
        # Get user info from JWT
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({'error': 'Invalid token'}), 401
            
        # Check if user is admin
        from src.models.user import User
        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
            
        return f(*args, **kwargs)
    return decorated_function

def init_change_tracking_table():
    """Initialize the change tracking table if it doesn't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_name TEXT,
            erf_number TEXT,
            change_type TEXT NOT NULL,
            field_name TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            change_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            admin_reviewed BOOLEAN DEFAULT FALSE,
            admin_reviewer TEXT,
            review_timestamp DATETIME,
            exported_to_external BOOLEAN DEFAULT FALSE,
            export_timestamp DATETIME,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create index for faster queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_user_changes_timestamp 
        ON user_changes (change_timestamp DESC)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_user_changes_reviewed 
        ON user_changes (admin_reviewed, change_timestamp DESC)
    ''')
    
    conn.commit()
    conn.close()

def log_user_change(user_id, user_name, erf_number, change_type, field_name, old_value, new_value):
    """Log a user change to the tracking table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO user_changes 
        (user_id, user_name, erf_number, change_type, field_name, old_value, new_value)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, user_name, erf_number, change_type, field_name, old_value, new_value))
    
    conn.commit()
    conn.close()

@admin_notifications.route('/admin/changes/pending', methods=['GET'])
@admin_required
def get_pending_changes():
    """Get all unreviewed changes, prioritizing critical fields"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Critical fields that need immediate attention
        critical_fields = ['cellphone_number', 'vehicle_registration', 'vehicle_registration_2']
        
        cursor.execute('''
            SELECT 
                id, user_id, user_name, erf_number, change_type, field_name, 
                old_value, new_value, change_timestamp, notes,
                CASE 
                    WHEN field_name IN ('cellphone_number', 'vehicle_registration', 'vehicle_registration_2') 
                    THEN 'critical' 
                    ELSE 'normal' 
                END as priority
            FROM user_changes 
            WHERE admin_reviewed = FALSE 
            ORDER BY 
                CASE 
                    WHEN field_name IN ('cellphone_number', 'vehicle_registration', 'vehicle_registration_2') 
                    THEN 0 
                    ELSE 1 
                END,
                change_timestamp DESC
        ''')
        
        changes = []
        for row in cursor.fetchall():
            changes.append({
                'id': row[0],
                'user_id': row[1],
                'user_name': row[2],
                'erf_number': row[3],
                'change_type': row[4],
                'field_name': row[5],
                'old_value': row[6],
                'new_value': row[7],
                'change_timestamp': row[8],
                'notes': row[9],
                'priority': row[10]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'changes': changes,
            'total_pending': len(changes),
            'critical_pending': len([c for c in changes if c['priority'] == 'critical'])
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch pending changes: {str(e)}'}), 500

@admin_notifications.route('/admin/changes/critical', methods=['GET'])
@admin_required
def get_critical_changes():
    """Get only critical changes (cellphone and vehicle registration)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                id, user_id, user_name, erf_number, change_type, field_name, 
                old_value, new_value, change_timestamp, admin_reviewed, notes
            FROM user_changes 
            WHERE field_name IN ('cellphone_number', 'vehicle_registration', 'vehicle_registration_2')
            AND admin_reviewed = FALSE
            ORDER BY change_timestamp DESC
        ''')
        
        changes = []
        for row in cursor.fetchall():
            changes.append({
                'id': row[0],
                'user_id': row[1],
                'user_name': row[2],
                'erf_number': row[3],
                'change_type': row[4],
                'field_name': row[5],
                'old_value': row[6],
                'new_value': row[7],
                'change_timestamp': row[8],
                'admin_reviewed': row[9],
                'notes': row[10]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'critical_changes': changes,
            'count': len(changes)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch critical changes: {str(e)}'}), 500

@admin_notifications.route('/admin/changes/review', methods=['POST'])
@admin_required
def review_changes():
    """Mark changes as reviewed by admin"""
    try:
        data = request.json
        change_ids = data.get('change_ids', [])
        notes = data.get('notes', '')
        
        if not change_ids:
            return jsonify({'error': 'No change IDs provided'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Mark changes as reviewed
        placeholders = ','.join(['?' for _ in change_ids])
        # Get admin username from JWT
        user_id = get_jwt_identity()
        from src.models.user import User
        admin_user = User.query.get(user_id)
        admin_username = admin_user.email if admin_user else 'Unknown Admin'
        
        cursor.execute(f'''
            UPDATE user_changes 
            SET admin_reviewed = TRUE, 
                admin_reviewer = ?, 
                review_timestamp = CURRENT_TIMESTAMP,
                notes = COALESCE(notes || ' | ' || ?, ?)
            WHERE id IN ({placeholders})
        ''', [admin_username] + [notes, notes] + change_ids)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Reviewed {len(change_ids)} changes',
            'reviewed_by': admin_username
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to review changes: {str(e)}'}), 500

@admin_notifications.route('/admin/changes/export-critical', methods=['GET'])
@admin_required
def export_critical_data():
    """Export critical data for external systems (Accentronix & Camera System)"""
    try:
        export_type = request.args.get('type', 'all')  # 'accentronix', 'camera', or 'all'
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get users with recent critical changes
        if export_type == 'accentronix':
            # Export cellphone data for Accentronix gate system
            cursor.execute('''
                SELECT DISTINCT u.id, u.full_name, u.erf_number, u.cellphone_number,
                       MAX(uc.change_timestamp) as last_change
                FROM users u
                LEFT JOIN user_changes uc ON u.id = uc.user_id 
                WHERE u.cellphone_number IS NOT NULL 
                AND u.cellphone_number != ''
                AND (uc.field_name = 'cellphone_number' OR uc.field_name IS NULL)
                GROUP BY u.id, u.full_name, u.erf_number, u.cellphone_number
                ORDER BY last_change DESC, u.erf_number
            ''')
            
            export_data = []
            for row in cursor.fetchall():
                export_data.append({
                    'erf_number': row[2],
                    'resident_name': row[1],
                    'cellphone_number': row[3],
                    'intercom_code': f"ERF{row[2][:4]}",  # Generate intercom code
                    'last_updated': row[4] or 'Initial data'
                })
                
            return jsonify({
                'success': True,
                'export_type': 'accentronix_gate_system',
                'data': export_data,
                'count': len(export_data),
                'instructions': 'Import this data into your Accentronix gate system for intercom codes'
            })
            
        elif export_type == 'camera':
            # Export vehicle registration data for camera system
            cursor.execute('''
                SELECT DISTINCT u.id, u.full_name, u.erf_number, 
                       u.vehicle_registration, u.vehicle_registration_2,
                       MAX(uc.change_timestamp) as last_change
                FROM users u
                LEFT JOIN user_changes uc ON u.id = uc.user_id 
                WHERE (u.vehicle_registration IS NOT NULL AND u.vehicle_registration != '')
                   OR (u.vehicle_registration_2 IS NOT NULL AND u.vehicle_registration_2 != '')
                AND (uc.field_name IN ('vehicle_registration', 'vehicle_registration_2') OR uc.field_name IS NULL)
                GROUP BY u.id, u.full_name, u.erf_number, u.vehicle_registration, u.vehicle_registration_2
                ORDER BY last_change DESC, u.erf_number
            ''')
            
            export_data = []
            for row in cursor.fetchall():
                # Add primary vehicle
                if row[3]:  # vehicle_registration
                    export_data.append({
                        'erf_number': row[2],
                        'resident_name': row[1],
                        'vehicle_registration': row[3],
                        'vehicle_type': 'primary',
                        'last_updated': row[5] or 'Initial data'
                    })
                
                # Add secondary vehicle
                if row[4]:  # vehicle_registration_2
                    export_data.append({
                        'erf_number': row[2],
                        'resident_name': row[1],
                        'vehicle_registration': row[4],
                        'vehicle_type': 'secondary',
                        'last_updated': row[5] or 'Initial data'
                    })
            
            return jsonify({
                'success': True,
                'export_type': 'camera_identification_system',
                'data': export_data,
                'count': len(export_data),
                'instructions': 'Import this data into your camera system for automated boom gate access'
            })
            
        else:  # export_type == 'all'
            # Export both datasets
            # ... (implement combined export)
            return jsonify({
                'success': True,
                'message': 'Use ?type=accentronix or ?type=camera for specific exports'
            })
        
        conn.close()
        
    except Exception as e:
        return jsonify({'error': f'Failed to export data: {str(e)}'}), 500

@admin_notifications.route('/admin/changes/mark-exported', methods=['POST'])
@admin_required
def mark_as_exported():
    """Mark changes as exported to external systems"""
    try:
        data = request.json
        change_ids = data.get('change_ids', [])
        export_type = data.get('export_type', 'manual')
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        placeholders = ','.join(['?' for _ in change_ids])
        cursor.execute(f'''
            UPDATE user_changes 
            SET exported_to_external = TRUE, 
                export_timestamp = CURRENT_TIMESTAMP,
                notes = COALESCE(notes || ' | Exported to ' || ?, 'Exported to ' || ?)
            WHERE id IN ({placeholders})
        ''', [export_type, export_type] + change_ids)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Marked {len(change_ids)} changes as exported to {export_type}'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to mark as exported: {str(e)}'}), 500

@admin_notifications.route('/admin/changes/stats', methods=['GET'])
@admin_required
def get_change_stats():
    """Get statistics about recent changes"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get stats for different time periods
        stats = {}
        
        # Today's changes
        cursor.execute('''
            SELECT COUNT(*) FROM user_changes 
            WHERE DATE(change_timestamp) = DATE('now')
        ''')
        stats['today'] = cursor.fetchone()[0]
        
        # This week's changes
        cursor.execute('''
            SELECT COUNT(*) FROM user_changes 
            WHERE change_timestamp >= DATE('now', '-7 days')
        ''')
        stats['this_week'] = cursor.fetchone()[0]
        
        # Critical changes pending
        cursor.execute('''
            SELECT COUNT(*) FROM user_changes 
            WHERE field_name IN ('cellphone_number', 'vehicle_registration', 'vehicle_registration_2')
            AND admin_reviewed = FALSE
        ''')
        stats['critical_pending'] = cursor.fetchone()[0]
        
        # Total unreviewed
        cursor.execute('''
            SELECT COUNT(*) FROM user_changes 
            WHERE admin_reviewed = FALSE
        ''')
        stats['total_pending'] = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get stats: {str(e)}'}), 500

# Initialize the change tracking table when the module is imported
init_change_tracking_table()
