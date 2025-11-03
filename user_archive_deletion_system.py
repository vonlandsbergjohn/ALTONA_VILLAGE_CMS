#!/usr/bin/env python3
"""
User Archive and Deletion System for Altona Village CMS
Handles archiving and deletion of inactive users based on their roles and status
"""

import psycopg2
import os
from datetime import datetime, timedelta
import uuid
import json

class UserArchiveDeletionSystem:
    def __init__(self, db_path=None):
        self.db_url = os.getenv('DATABASE_URL', "postgresql://postgres:%23Johnvonl1977@localhost:5432/altona_village_db")
    
    def _table_exists(self, cursor, table_name):
        """Check if a table exists in the database."""
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = %s
            )
        """, (table_name,))
        return cursor.fetchone()[0]
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_url)
    
    def get_inactive_users_analysis(self):
        """Analyze inactive users and their data retention requirements"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        print("🔍 INACTIVE USERS ANALYSIS")
        print("=" * 60)
        
        # Get users with completed transition requests (terminated)
        cursor.execute("""
            SELECT DISTINCT u.id, u.email, u.role, u.status, u.archived,
                   r.first_name as resident_first, r.last_name as resident_last, 
                   r.erf_number as resident_erf, r.status as resident_status,
                   o.first_name as owner_first, o.last_name as owner_last,
                   o.erf_number as owner_erf, o.status as owner_status,
                   utr.status as transition_status, utr.new_occupant_type
            FROM users u
            LEFT JOIN residents r ON u.id = r.user_id
            LEFT JOIN owners o ON u.id = o.user_id
            LEFT JOIN user_transition_requests utr ON u.id = utr.user_id
            WHERE utr.status = 'completed' AND utr.new_occupant_type = 'terminated'
               OR r.status IN ('inactive', 'deleted_profile')
               OR o.status IN ('inactive', 'deleted_profile')
               OR u.status IN ('inactive', 'suspended')
        """)
        
        inactive_users = cursor.fetchall()
        
        analysis_results = []
        
        for user_data in inactive_users:
            user_analysis = self._analyze_user_for_archival(cursor, user_data)
            analysis_results.append(user_analysis)
            
            print(f"\n👤 User: {user_analysis['email']} ({user_analysis['user_role']})")
            print(f"   User Status: {user_analysis['user_status']}")
            print(f"   User Type: {user_analysis['user_type']}")
            print(f"   Archive Action: {user_analysis['recommended_action']}")
            print(f"   Retention Period: {user_analysis['retention_period']}")
            print(f"   Data to Preserve: {', '.join(user_analysis['data_to_preserve'])}")
            print(f"   Data to Delete: {', '.join(user_analysis['data_to_delete'])}")
            
            if user_analysis['vehicles']:
                print(f"   Vehicles: {len(user_analysis['vehicles'])} registered")
            if user_analysis['complaints']:
                print(f"   Complaints: {len(user_analysis['complaints'])} total")
        
        conn.close()
        return analysis_results
    
    def _analyze_user_for_archival(self, cursor, user_data):
        """Analyze a single user for archival/deletion requirements"""
        user_id, email, role, user_status, archived = user_data[:5]
        resident_first, resident_last, resident_erf, resident_status = user_data[5:9]
        owner_first, owner_last, owner_erf, owner_status = user_data[9:13]
        transition_status, new_occupant_type = user_data[13:15]
        
        # Determine user type
        is_resident = resident_first is not None
        is_owner = owner_first is not None
        
        if is_resident and is_owner:
            user_type = "owner_resident"
        elif is_resident:
            user_type = "tenant_only"
        elif is_owner:
            user_type = "owner_only"
        else:
            user_type = "unknown"
        
        # Get additional data
        vehicles = self._get_user_vehicles(cursor, user_id)
        complaints = self._get_user_complaints(cursor, user_id)
        
        # Determine recommended action based on user type and regulations
        if user_type == "tenant_only":
            recommended_action = "immediate_deletion"
            retention_period = "None - Delete immediately"
            data_to_preserve = []
            data_to_delete = ["personal_info", "vehicles", "access_codes", "emergency_contacts", "complaints"]
            
        elif user_type == "owner_only":
            recommended_action = "archive_with_limited_retention"
            retention_period = "2 years - Property history only"
            data_to_preserve = ["property_ownership_dates", "erf_association", "title_deed_info"]
            data_to_delete = ["personal_details", "emergency_contacts", "vehicles", "access_codes", "postal_address"]
            
        elif user_type == "owner_resident":
            # Check if they sold property or just moved out
            if transition_status == "completed" and new_occupant_type == "terminated":
                recommended_action = "immediate_deletion"  # Sold property
                retention_period = "None - Sold property"
                data_to_preserve = []
                data_to_delete = ["all_data"]
            else:
                recommended_action = "archive_resident_keep_owner"  # Moved out but kept property
                retention_period = "Resident: 30 days, Owner: Active"
                data_to_preserve = ["property_ownership", "title_deed_info"]
                data_to_delete = ["resident_personal_info", "emergency_contacts", "access_codes"]
        else:
            recommended_action = "manual_review"
            retention_period = "Requires manual review"
            data_to_preserve = ["review_required"]
            data_to_delete = ["review_required"]
        
        return {
            'user_id': user_id,
            'email': email,
            'user_role': role,
            'user_status': user_status,
            'user_type': user_type,
            'archived': bool(archived),
            'resident_erf': resident_erf,
            'owner_erf': owner_erf,
            'recommended_action': recommended_action,
            'retention_period': retention_period,
            'data_to_preserve': data_to_preserve,
            'data_to_delete': data_to_delete,
            'vehicles': vehicles,
            'complaints': complaints,
            'transition_status': transition_status,
            'new_occupant_type': new_occupant_type
        }
    
    def _get_user_vehicles(self, cursor, user_id):
        """Get all vehicles associated with user"""
        cursor.execute("""
            SELECT id, registration_number, make, model, color, status
            FROM vehicles 
            WHERE resident_id = %s OR owner_id = %s
        """, (str(user_id), str(user_id)))
        return cursor.fetchall()
    
    def _get_user_complaints(self, cursor, user_id):
        """Get all complaints associated with user"""
        cursor.execute("""
            SELECT id, subject, status, created_at
            FROM complaints 
            WHERE resident_id = %s
        """, (str(user_id),))
        return cursor.fetchall()
    
    def archive_user(self, user_id, archive_reason, performed_by_admin_id):
        """Archive a user with proper data retention"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get user analysis first
            cursor.execute("""
                SELECT u.id, u.email, u.role, u.status, u.archived,
                       r.first_name as resident_first, r.last_name as resident_last, 
                       r.erf_number as resident_erf, r.status as resident_status,
                       o.first_name as owner_first, o.last_name as owner_last,
                       o.erf_number as owner_erf, o.status as owner_status,
                       utr.status as transition_status, utr.new_occupant_type
                FROM users u
                LEFT JOIN residents r ON u.id = r.user_id
                LEFT JOIN owners o ON u.id = o.user_id
                LEFT JOIN user_transition_requests utr ON u.id = utr.user_id
                WHERE u.id = ?
            """, (str(user_id),))
            
            user_data = cursor.fetchone()
            if not user_data:
                raise ValueError(f"User {user_id} not found")
            
            analysis = self._analyze_user_for_archival(cursor, user_data)
            
            print(f"🗄️ Archiving user: {analysis['email']}")
            print(f"   Type: {analysis['user_type']}")
            print(f"   Action: {analysis['recommended_action']}")
            
            # Create archive record before deletion
            archive_data = self._create_archive_record(cursor, user_id, analysis, archive_reason, performed_by_admin_id)
            
            # Perform archival actions based on user type
            if analysis['recommended_action'] == 'immediate_deletion':
                self._perform_immediate_deletion(cursor, user_id, analysis)
            elif analysis['recommended_action'] == 'archive_with_limited_retention':
                self._perform_limited_retention_archive(cursor, user_id, analysis)
            elif analysis['recommended_action'] == 'archive_resident_keep_owner':
                self._perform_resident_archive_keep_owner(cursor, user_id, analysis)
            else:
                print(f"   ⚠️ Manual review required for {analysis['email']}")
                return False
            
            # Mark user as archived
            cursor.execute("""
                UPDATE users SET 
                    archived = 1, 
                    archived_at = ?, 
                    archived_by = ?,
                    archive_reason = ?,
                    status = 'archived'
                WHERE id = %s
            """, (datetime.now(), performed_by_admin_id, archive_reason, str(user_id)))
            
            conn.commit()
            print(f"   ✅ User {analysis['email']} archived successfully")
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"   ❌ Error archiving user: {e}")
            return False
        finally:
            conn.close()
    
    def _create_archive_record(self, cursor, user_id, analysis, archive_reason, performed_by_admin_id):
        """Create a comprehensive archive record before deletion"""
        
        # Get complete user data for archival
        cursor.execute("""
            SELECT u.*, r.*, o.*
            FROM users u
            LEFT JOIN residents r ON u.id = r.user_id
            LEFT JOIN owners o ON u.id = o.user_id
            WHERE u.id = ?
        """, (str(user_id),))
        
        user_data = cursor.fetchone()
        
        archive_record = {
            'archive_id': str(uuid.uuid4()),
            'user_id': user_id,
            'archived_at': datetime.now(),
            'archived_by': performed_by_admin_id,
            'archive_reason': archive_reason,
            'user_type': analysis['user_type'],
            'retention_policy': analysis['recommended_action'],
            'data_preserved': analysis['data_to_preserve'],
            'data_deleted': analysis['data_to_delete'],
            'vehicles': analysis['vehicles'],
            'complaints': analysis['complaints'],
            'original_data': {
                'user': dict(zip([col[0] for col in cursor.description], user_data)) if user_data else None
            }
        }
        
        # Store archive record in dedicated table (create if doesn't exist)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_archives (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36),
                archived_at TIMESTAMP,
                archived_by VARCHAR(36),
                archive_reason TEXT,
                user_type VARCHAR(50),
                retention_policy VARCHAR(100),
                archive_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            INSERT INTO user_archives (id, user_id, archived_at, archived_by, archive_reason, user_type, retention_policy, archive_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            archive_record['archive_id'],
            user_id,
            archive_record['archived_at'],
            performed_by_admin_id,
            archive_reason,
            analysis['user_type'],
            analysis['recommended_action'],
            json.dumps(archive_record)
        ))
        
        print(f"   📦 Archive record created: {archive_record['archive_id']}")
        return archive_record
    
    def _perform_immediate_deletion(self, cursor, user_id, analysis):
        """Perform immediate deletion for tenants and sold property owners"""
        print(f"   🗑️ Performing immediate deletion for {analysis['user_type']}")
        
        # Delete vehicles
        cursor.execute("DELETE FROM vehicles WHERE resident_id = %s OR owner_id = %s", (str(user_id), str(user_id)))
        vehicle_count = cursor.rowcount
        
        # Delete complaints and updates
        cursor.execute("DELETE FROM complaint_updates WHERE complaint_id IN (SELECT id FROM complaints WHERE resident_id = %s)", (str(user_id),))
        cursor.execute("DELETE FROM complaints WHERE resident_id = %s", (str(user_id),))
        complaint_count = cursor.rowcount
        
        # Delete resident record
        if analysis['user_type'] in ['tenant_only', 'owner_resident']:
            cursor.execute("DELETE FROM residents WHERE user_id = %s", (str(user_id),))
            resident_deleted = cursor.rowcount > 0
        else:
            resident_deleted = False
        
        # Delete owner record (only if they sold the property)
        if analysis['user_type'] in ['owner_resident'] and analysis['new_occupant_type'] == 'terminated':
            cursor.execute("DELETE FROM owners WHERE user_id = %s", (str(user_id),))
            owner_deleted = cursor.rowcount > 0
        else:
            owner_deleted = False
        
        print(f"      ✅ Deleted {vehicle_count} vehicles")
        print(f"      ✅ Deleted {complaint_count} complaints")
        if resident_deleted:
            print(f"      ✅ Deleted resident record")
        if owner_deleted:
            print(f"      ✅ Deleted owner record")
    
    def _perform_limited_retention_archive(self, cursor, user_id, analysis):
        """Archive owner with limited data retention"""
        print(f"   📦 Performing limited retention archive for {analysis['user_type']}")
        
        # Delete vehicles (owners don't need vehicle access after selling)
        cursor.execute("DELETE FROM vehicles WHERE resident_id = %s OR owner_id = %s", (str(user_id), str(user_id)))
        vehicle_count = cursor.rowcount
        
        # Update owner record to remove personal details but keep property history
        cursor.execute("""
            UPDATE owners SET 
                phone_number = NULL,
                emergency_contact_name = NULL,
                emergency_contact_number = NULL,
                postal_street_number = NULL,
                postal_street_name = NULL,
                postal_suburb = NULL,
                postal_city = NULL,
                postal_code = NULL,
                postal_province = NULL,
                full_postal_address = NULL,
                status = 'archived',
                migration_date = ?,
                migration_reason = 'Limited retention - property history only'
            WHERE user_id = %s
        """, (datetime.now(), str(user_id)))
        
        print(f"      ✅ Deleted {vehicle_count} vehicles")
        print(f"      ✅ Archived owner record with limited data")
    
    def _perform_resident_archive_keep_owner(self, cursor, user_id, analysis):
        """Archive resident data but keep owner data active"""
        print(f"   📦 Archiving resident data, keeping owner active")
        
        # Update resident status to archived
        cursor.execute("""
            UPDATE residents SET 
                status = 'archived',
                moving_out_date = ?,
                migration_date = ?,
                migration_reason = 'Moved out but retained ownership'
            WHERE user_id = %s
        """, (datetime.now().date(), datetime.now(), str(user_id)))
        
        # Update vehicles to reflect non-resident status
        cursor.execute("""
            UPDATE vehicles SET 
                status = 'owner_access_only',
                updated_at = ?
            WHERE resident_id = %s OR owner_id = %s
        """, (datetime.now(), str(user_id), str(user_id)))
        
        vehicle_count = cursor.rowcount
        
        print(f"      ✅ Archived resident record")
        print(f"      ✅ Updated {vehicle_count} vehicles to owner-only access")
        print(f"      ✅ Owner record remains active")
    
    def get_archived_users(self, days_since_archive=None):
        """Get list of archived users, optionally filtered by archive date"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        base_query = """
            SELECT ua.id, ua.user_id, ua.archived_at, ua.archived_by, 
                   ua.archive_reason, ua.user_type, ua.retention_policy,
                   u.email, u.status
            FROM user_archives ua
            LEFT JOIN users u ON ua.user_id = u.id
        """
        
        if days_since_archive:
            cutoff_date = datetime.now() - timedelta(days=days_since_archive)
            query = base_query + " WHERE ua.archived_at >= %s"
            cursor.execute(query, (cutoff_date,))
        else:
            cursor.execute(base_query)
        
        archived_users = cursor.fetchall()
        conn.close()
        
        return archived_users
    
    def cleanup_old_archives(self, retention_days=730):  # 2 years default
        """Clean up old archive records based on retention policy"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        # Get archives to be deleted
        cursor.execute("""
            SELECT id, user_type, archived_at 
            FROM user_archives 
            WHERE archived_at < %s
        """, (cutoff_date,))
        
        old_archives = cursor.fetchall()
        
        if old_archives:
            print(f"🧹 Cleaning up {len(old_archives)} old archive records (older than {retention_days} days)")
            
            # Delete old archive records
            cursor.execute("DELETE FROM user_archives WHERE archived_at < %s", (cutoff_date,))
            deleted_count = cursor.rowcount
            
            conn.commit()
            print(f"   ✅ Deleted {deleted_count} old archive records")
        else:
            print("🧹 No old archive records to clean up")
        
        conn.close()
        return len(old_archives) if old_archives else 0

    def permanently_delete_user(self, user_id, deletion_reason, performed_by_admin_id, confirm_deletion=False):
        """
        Permanently delete a user from the system completely.
        This is for cases where users were incorrectly approved or registered by mistake.
        
        WARNING: This is a PERMANENT deletion that cannot be undone!
        Use this only for incorrect registrations, not for regular user lifecycle management.
        """
        if not confirm_deletion:
            print("⚠️  WARNING: This will PERMANENTLY delete all user data!")
            print("   This action cannot be undone and should only be used for:")
            print("   - Incorrectly approved registrations")
            print("   - Mistaken registrations")
            print("   - Users who should never have been in the system")
            print("   ")
            print("   To confirm deletion, call this function with confirm_deletion=True")
            return False
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # First, get complete user information for logging
            cursor.execute("""
                SELECT u.id, u.email, u.role, u.status, u.created_at,
                       r.first_name as resident_first, r.last_name as resident_last, 
                       r.erf_number as resident_erf, r.phone_number as resident_phone,
                       o.first_name as owner_first, o.last_name as owner_last,
                       o.erf_number as owner_erf, o.phone_number as owner_phone
                FROM users u
                LEFT JOIN residents r ON u.id = r.user_id
                LEFT JOIN owners o ON u.id = o.user_id
                WHERE u.id = ?
            """, (user_id,))
            
            user_data = cursor.fetchone()
            if not user_data:
                raise ValueError(f"User {user_id} not found")
            
            user_email = user_data[1]
            user_role = user_data[2]
            resident_name = f"{user_data[5]} {user_data[6]}" if user_data[5] else None
            owner_name = f"{user_data[9]} {user_data[10]}" if user_data[9] else None
            
            print(f"🗑️ PERMANENTLY DELETING USER: {user_email}")
            print(f"   Role: {user_role}")
            if resident_name:
                print(f"   Resident: {resident_name} (ERF {user_data[7]})")
            if owner_name:
                print(f"   Owner: {owner_name} (ERF {user_data[11]})")
            print(f"   Reason: {deletion_reason}")
            
            # Create deletion log before removing data
            deletion_record = self._create_deletion_log(cursor, user_id, user_data, deletion_reason, performed_by_admin_id)
            
            # Get counts for reporting
            deletion_summary = self._get_user_data_counts(cursor, user_id)
            
            # Step 1: Delete all related data in correct order (foreign keys)
            print("   🗑️ Deleting related data...")
            
            # Delete complaint updates first (references complaints)
            cursor.execute("""
                DELETE FROM complaint_updates 
                WHERE complaint_id IN (SELECT id FROM complaints WHERE resident_id = ?)
            """, (user_id,))
            complaint_updates_deleted = cursor.rowcount
            
            # Delete complaints
            cursor.execute("DELETE FROM complaints WHERE resident_id = ?", (user_id,))
            complaints_deleted = cursor.rowcount
            
            # Delete vehicles
            cursor.execute("DELETE FROM vehicles WHERE resident_id = ? OR owner_id = ?", (user_id, user_id))
            vehicles_deleted = cursor.rowcount
            
            # Delete transition requests
            cursor.execute("DELETE FROM user_transition_requests WHERE user_id = ?", (user_id,))
            transitions_deleted = cursor.rowcount
            
            # Delete any pending registrations (if table exists)
            pending_deleted = 0
            if self._table_exists(cursor, 'pending_registrations'):
                cursor.execute("DELETE FROM pending_registrations WHERE email = ?", (user_email,))
                pending_deleted = cursor.rowcount
            
            # Delete password reset tokens (if table exists)
            tokens_deleted = 0
            if self._table_exists(cursor, 'password_reset_tokens'):
                cursor.execute("DELETE FROM password_reset_tokens WHERE user_id = ?", (user_id,))
                tokens_deleted = cursor.rowcount
            
            # Delete user sessions (if table exists)
            sessions_deleted = 0
            if self._table_exists(cursor, 'user_sessions'):
                cursor.execute("DELETE FROM user_sessions WHERE user_id = ?", (user_id,))
                sessions_deleted = cursor.rowcount
            
            # Step 2: Delete profile records
            print("   🗑️ Deleting profile records...")
            
            # Delete resident record
            cursor.execute("DELETE FROM residents WHERE user_id = ?", (user_id,))
            resident_deleted = cursor.rowcount > 0
            
            # Delete owner record
            cursor.execute("DELETE FROM owners WHERE user_id = ?", (user_id,))
            owner_deleted = cursor.rowcount > 0
            
            # Step 3: Delete user record itself
            print("   🗑️ Deleting user account...")
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            user_deleted = cursor.rowcount > 0
            
            if not user_deleted:
                raise ValueError("Failed to delete user record")
            
            # Commit all deletions
            conn.commit()
            
            # Report deletion summary
            print(f"   ✅ USER PERMANENTLY DELETED: {user_email}")
            print(f"      📧 User account: Deleted")
            if resident_deleted:
                print(f"      🏠 Resident profile: Deleted")
            if owner_deleted:
                print(f"      🏡 Owner profile: Deleted")
            print(f"      🚗 Vehicles: {vehicles_deleted} deleted")
            print(f"      📋 Complaints: {complaints_deleted} deleted")
            print(f"      💬 Complaint updates: {complaint_updates_deleted} deleted")
            print(f"      🔄 Transition requests: {transitions_deleted} deleted")
            print(f"      ⏳ Pending registrations: {pending_deleted} deleted")
            print(f"      🔑 Password tokens: {tokens_deleted} deleted")
            print(f"      🖥️ User sessions: {sessions_deleted} deleted")
            print(f"      📝 Deletion logged: {deletion_record['deletion_id']}")
            
            return {
                'success': True,
                'user_email': user_email,
                'deletion_id': deletion_record['deletion_id'],
                'summary': {
                    'user_deleted': user_deleted,
                    'resident_deleted': resident_deleted,
                    'owner_deleted': owner_deleted,
                    'vehicles_deleted': vehicles_deleted,
                    'complaints_deleted': complaints_deleted,
                    'complaint_updates_deleted': complaint_updates_deleted,
                    'transitions_deleted': transitions_deleted,
                    'pending_deleted': pending_deleted,
                    'tokens_deleted': tokens_deleted,
                    'sessions_deleted': sessions_deleted
                }
            }
            
        except Exception as e:
            conn.rollback()
            print(f"   ❌ Error during permanent deletion: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            conn.close()
    
    def _create_deletion_log(self, cursor, user_id, user_data, deletion_reason, performed_by_admin_id):
        """Create a log record of the permanent deletion for audit purposes"""
        
        deletion_record = {
            'deletion_id': str(uuid.uuid4()),
            'user_id': user_id,
            'deleted_at': datetime.now(),
            'deleted_by': performed_by_admin_id,
            'deletion_reason': deletion_reason,
            'deletion_type': 'permanent_admin_deletion',
            'original_user_data': {
                'email': user_data[1],
                'role': user_data[2],
                'status': user_data[3],
                'created_at': user_data[4],
                'resident_name': f"{user_data[5]} {user_data[6]}" if user_data[5] else None,
                'resident_erf': user_data[7],
                'owner_name': f"{user_data[9]} {user_data[10]}" if user_data[9] else None,
                'owner_erf': user_data[11]
            }
        }
        
        # Create deletion log table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_deletion_log (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36),
                deleted_at TIMESTAMP,
                deleted_by VARCHAR(36),
                deletion_reason TEXT,
                deletion_type VARCHAR(100),
                original_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            INSERT INTO user_deletion_log (id, user_id, deleted_at, deleted_by, deletion_reason, deletion_type, original_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            deletion_record['deletion_id'],
            user_id,
            deletion_record['deleted_at'],
            performed_by_admin_id,
            deletion_reason,
            deletion_record['deletion_type'],
            json.dumps(deletion_record)
        ))
        
        return deletion_record
    
    def _get_user_data_counts(self, cursor, user_id):
        """Get counts of all related data for reporting"""
        counts = {}
        
        # Count vehicles
        cursor.execute("SELECT COUNT(*) FROM vehicles WHERE resident_id = %s OR owner_id = %s", (str(user_id), str(user_id)))
        counts['vehicles'] = cursor.fetchone()[0]
        
        # Count complaints
        cursor.execute("SELECT COUNT(*) FROM complaints WHERE resident_id = %s", (str(user_id),))
        counts['complaints'] = cursor.fetchone()[0]
        
        # Count transition requests
        cursor.execute("SELECT COUNT(*) FROM user_transition_requests WHERE user_id = %s", (str(user_id),))
        counts['transitions'] = cursor.fetchone()[0]
        
        return counts
    
    def get_deletion_logs(self, days_back=30):
        """Get recent deletion logs for audit purposes"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        cursor.execute("""
            SELECT id, user_id, deleted_at, deleted_by, deletion_reason, deletion_type, original_data
            FROM user_deletion_log
            WHERE deleted_at >= ?
            ORDER BY deleted_at DESC;
        """, (cutoff_date,))
        
        deletion_logs = cursor.fetchall()
        conn.close()
        
        return deletion_logs
    
    def verify_user_completely_deleted(self, user_email):
        """Verify that a user has been completely removed from all tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        print(f"🔍 Verifying complete deletion of: {user_email}")
        
        # Check all tables that might contain user data
        tables_to_check = [
            ('users', 'email'),
            ('residents', 'user_id'),
            ('owners', 'user_id'),
            ('vehicles', 'resident_id'),
            ('vehicles', 'owner_id'),
            ('complaints', 'resident_id'),
            ('user_transition_requests', 'user_id'),
            ('pending_registrations', 'email'),
            ('password_reset_tokens', 'user_id'),
            ('user_sessions', 'user_id')
        ]
        
        found_data = []
        
        for table, column in tables_to_check:
            # Check if table exists before querying
            if not self._table_exists(cursor, table):
                print(f"   ⚠️ Table '{table}' does not exist, skipping verification")
                continue
                
            try:
                if column == 'email':
                    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} = %s", (user_email,))
                else:
                    # For user_id columns, we need to first get the user_id from email
                    cursor.execute("SELECT id FROM users WHERE email = %s", (user_email,))
                    user_result = cursor.fetchone()
                    if user_result:
                        user_id = user_result[0]
                        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} = %s", (str(user_id),))
                    else:
                        # User doesn't exist, so count will be 0
                        cursor.execute("SELECT 0")
                
                count = cursor.fetchone()[0]
                if count > 0:
                    found_data.append((table, column, count))
                    print(f"   ❌ Found {count} records in {table}.{column}")
                else:
                    print(f"   ✅ No records in {table}.{column}")
                    
            except psycopg2.Error as e:
                print(f"   ⚠️ Could not check {table}.{column}: {e}")
        
        conn.close()
        
        if found_data:
            print(f"   ❌ DELETION INCOMPLETE: Found data in {len(found_data)} locations")
            return False
        else:
            print(f"   ✅ DELETION VERIFIED: No traces of {user_email} found")
            return True

def main():
    """Main function to demonstrate the archive system"""
    system = UserArchiveDeletionSystem()
    
    print("🏠 ALTONA VILLAGE CMS - USER ARCHIVE & DELETION SYSTEM")
    print("=" * 60)
    
    # Analyze inactive users
    inactive_users = system.get_inactive_users_analysis()
    
    print(f"\n📊 SUMMARY")
    print("=" * 30)
    print(f"Total inactive users found: {len(inactive_users)}")
    
    # Group by action type
    action_summary = {}
    for user in inactive_users:
        action = user['recommended_action']
        if action not in action_summary:
            action_summary[action] = 0
        action_summary[action] += 1
    
    for action, count in action_summary.items():
        print(f"  {action}: {count} users")
    
    # Show archived users
    print(f"\n📦 ARCHIVED USERS")
    print("=" * 30)
    archived = system.get_archived_users()
    if archived:
        for archive in archived:
            print(f"  {archive[7]} - {archive[5]} - Archived: {archive[2][:10]}")
    else:
        print("  No archived users found")

if __name__ == "__main__":
    main()
