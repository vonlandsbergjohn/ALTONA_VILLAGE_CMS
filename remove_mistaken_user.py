#!/usr/bin/env python3
"""
Identify and Remove Mistaken User
Find the user that was created by mistake and remove them completely
"""

import psycopg2
import os
from datetime import datetime

DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://postgres:%23Johnvonl1977@localhost:5432/altona_village_db")

def identify_mistaken_user():
    """Identify the user that should be removed"""
    
    print("🔍 IDENTIFYING USERS FOR REMOVAL")
    print("=" * 60)
    
    conn = None
    users = []
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Get all users and their details
        cursor.execute("""
            SELECT u.id, u.email, u.role, u.status, u.created_at,
                   r.first_name as resident_first, r.last_name as resident_last, 
                   r.erf_number as resident_erf,
                   o.first_name as owner_first, o.last_name as owner_last,
                   o.erf_number as owner_erf
            FROM users u
            LEFT JOIN residents r ON u.id = r.user_id
            LEFT JOIN owners o ON u.id = o.user_id
            ORDER BY u.created_at
        """)
        
        users = cursor.fetchall()
        
        print(f"\nFound {len(users)} total users:")
        
        for i, user in enumerate(users, 1):
            user_id, email, role, status, created_at, res_first, res_last, res_erf, own_first, own_last, own_erf = user
            
            print(f"\n👤 User {i}: {email}")
            print(f"   ID: {user_id}")
            print(f"   Role: {role}, Status: {status}")
            print(f"   Created: {created_at}")
            
            if res_first:
                print(f"   🏠 Resident: {res_first} {res_last} (ERF {res_erf})")
            else:
                print(f"   🏠 No resident record")
                
            if own_first:
                print(f"   🏡 Owner: {own_first} {own_last} (ERF {own_erf})")
            else:
                print(f"   🏡 No owner record")
                
            # Check if user has any data
            cursor.execute("SELECT COUNT(*) FROM vehicles WHERE resident_id = %s OR owner_id = %s", (str(user_id), str(user_id)))
            vehicle_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM complaints WHERE resident_id = %s", (str(user_id),))
            complaint_count = cursor.fetchone()[0]
            
            print(f"   📊 Data: {vehicle_count} vehicles, {complaint_count} complaints")
            
            # Flag suspicious users (no resident/owner records)
            if not res_first and not own_first:
                print(f"   ⚠️ SUSPICIOUS: No resident or owner records - potential mistake!")
        
        print(f"\n❓ Which user should be permanently deleted?")
        print(f"   Please identify the user by email or position number")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()
    return users

def permanently_delete_user_by_email(email):
    """Permanently delete a user by email"""
    
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Find the user
        cursor.execute("SELECT id, email, role FROM users WHERE email = %s", (email,))
        user_result = cursor.fetchone()
        
        if not user_result:
            print(f"❌ User {email} not found")
            return False
        
        user_id, user_email, role = user_result
        
        print(f"🗑️ PERMANENTLY DELETING USER: {user_email}")
        print(f"   User ID: {user_id}")
        print(f"   Role: {role}")
        print(f"   ⚠️ WARNING: This action cannot be undone!")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_deletion_log (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36),
                deleted_at DATETIME,
                deleted_by VARCHAR(36),
                deletion_reason TEXT,
                deletion_type VARCHAR(100),
                original_data TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create deletion log first
        deletion_id = f"DEL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        cursor.execute("""
            INSERT INTO user_deletion_log (id, user_id, deleted_at, deleted_by, deletion_reason, deletion_type, original_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (deletion_id, str(user_id), datetime.now(), "admin", 
              "Mistaken user creation - not a real resident", "admin_cleanup", 
              f"{{\"email\": \"{user_email}\", \"role\": \"{role}\"}}"))
        
        # Delete in correct order to handle foreign keys
        
        # 1. Delete complaint updates
        cursor.execute("""
            DELETE FROM complaint_updates 
            WHERE complaint_id IN (SELECT id FROM complaints WHERE resident_id = %s)
        """, (str(user_id),))
        complaint_updates_deleted = cursor.rowcount
        
        # 2. Delete complaints
        cursor.execute("DELETE FROM complaints WHERE resident_id = %s", (str(user_id),))
        complaints_deleted = cursor.rowcount
        
        # 3. Delete vehicles
        cursor.execute("DELETE FROM vehicles WHERE resident_id = %s OR owner_id = %s", (str(user_id), str(user_id)))
        vehicles_deleted = cursor.rowcount
        
        # 4. Delete transition requests
        cursor.execute("DELETE FROM user_transition_requests WHERE user_id = %s", (str(user_id),))
        transitions_deleted = cursor.rowcount
        
        # 5. Delete resident record
        cursor.execute("DELETE FROM residents WHERE user_id = %s", (str(user_id),))
        resident_deleted = cursor.rowcount > 0
        
        # 6. Delete owner record
        cursor.execute("DELETE FROM owners WHERE user_id = %s", (str(user_id),))
        owner_deleted = cursor.rowcount > 0
        
        # 7. Finally delete user record
        cursor.execute("DELETE FROM users WHERE id = %s", (str(user_id),))
        user_deleted = cursor.rowcount > 0
        
        if not user_deleted:
            raise ValueError("Failed to delete user record")
        
        print(f"   ✅ USER PERMANENTLY DELETED")
        print(f"      📧 User account: Deleted")
        print(f"      🏠 Resident record: {'Deleted' if resident_deleted else 'None'}")
        print(f"      🏡 Owner record: {'Deleted' if owner_deleted else 'None'}")
        print(f"      🚗 Vehicles: {vehicles_deleted} deleted")
        print(f"      📋 Complaints: {complaints_deleted} deleted")
        print(f"      💬 Complaint updates: {complaint_updates_deleted} deleted")
        print(f"      🔄 Transition requests: {transitions_deleted} deleted")
        print(f"      📝 Deletion logged: {deletion_id}")
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"   ❌ Error during deletion: {e}")
        return False
    finally:
        if conn:
            conn.close()

def verify_deletion(email):
    """Verify the user was completely removed"""
    
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print(f"\n🔍 VERIFYING DELETION OF: {email}")
        
        # Check if user still exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE email = %s", (email,))
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            print(f"   ✅ User completely removed from database")
            
            # Check deletion log
            cursor.execute("""
                SELECT id, deleted_at, deletion_reason 
                FROM user_deletion_log 
                WHERE original_data LIKE %s
                ORDER BY deleted_at DESC LIMIT 1
            """, (f'%{email}%',))
            
            log_entry = cursor.fetchone()
            if log_entry:
                deletion_id, deleted_at, reason = log_entry
                print(f"   📝 Deletion logged: {deletion_id} at {deleted_at}")
                print(f"   📄 Reason: {reason}")
        else:
            print(f"   ❌ User still exists in database!")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    users = identify_mistaken_user()
    
    print(f"\n" + "="*60)
    print(f"To delete a user, specify their email address.")
    print(f"For example, if you want to delete the first user, note their email from the list above.")
    print(f"="*60)
