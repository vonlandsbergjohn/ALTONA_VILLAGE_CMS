#!/usr/bin/env python3
"""
Fix login issues by correcting user data inconsistencies.
"""

import sqlite3
import uuid
from datetime import datetime

def fix_login_issues():
    """Fix the user data inconsistencies causing login failures"""
    
    db_path = "altona_village_cms/src/database/app.db"
    
    print("🔧 Fixing Login Issues")
    print("=" * 50)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check current user and owner data
    cursor.execute("""
        SELECT u.id, u.email, u.role, u.status, o.id as owner_id, o.erf_number 
        FROM users u 
        LEFT JOIN owners o ON u.id = o.user_id 
        WHERE u.email = 'johanvonlandsberg080808@gmai.com'
    """)
    user_data = cursor.fetchall()
    
    print("📊 Current User Data:")
    for data in user_data:
        print(f"  User ID: {data[0]}, Email: {data[1]}, Role: {data[2]}, Owner ERF: {data[5]}")
    
    # Problem: Users have role='resident' but no resident records
    # Solution: Create resident records for users with resident role
    
    print("\n🔨 Creating Missing Resident Records...")
    
    for data in user_data:
        user_id = data[0]
        email = data[1]
        role = data[2]
        owner_id = data[4]
        erf_number = data[5]
        
        if role == 'resident' and owner_id:
            # Get owner data to copy to resident
            cursor.execute("SELECT * FROM owners WHERE user_id = ?", (user_id,))
            owner = cursor.fetchone()
            
            if owner:
                # Check if resident already exists
                cursor.execute("SELECT id FROM residents WHERE user_id = ?", (user_id,))
                existing_resident = cursor.fetchone()
                
                if not existing_resident:
                    # Create resident record based on owner data
                    resident_id = str(uuid.uuid4())
                    
                    insert_sql = """
                        INSERT INTO residents (
                            id, user_id, first_name, last_name, phone_number, 
                            id_number, erf_number, street_address, full_address,
                            gate_access, intercom_code, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    
                    now = datetime.now().isoformat()
                    
                    cursor.execute(insert_sql, (
                        resident_id, user_id, owner[3], owner[4], owner[5],  # id, user_id, first_name, last_name, phone
                        owner[6], owner[7], owner[8], owner[9],  # id_number, erf_number, street_address, full_address
                        'pending', '1234', 'pending', now, now  # gate_access, intercom_code, status, created_at, updated_at
                    ))
                    
                    print(f"  ✅ Created resident record for {email} - ERF {erf_number}")
                else:
                    print(f"  ℹ️ Resident record already exists for {email}")
    
    # Fix: Ensure users with owner records have correct data
    print("\n🔄 Updating User Roles Based on Data...")
    
    # Users should be 'owner' if they only have owner records
    # Users should be 'resident' if they have both resident and owner records
    cursor.execute("""
        UPDATE users 
        SET role = 'owner' 
        WHERE email = 'johanvonlandsberg080808@gmai.com' 
        AND id IN (SELECT user_id FROM owners)
        AND id NOT IN (SELECT user_id FROM residents)
    """)
    
    print(f"  ✅ Updated user roles based on data relationships")
    
    conn.commit()
    
    # Verify the fix
    print("\n✅ Verification - Updated User Data:")
    cursor.execute("""
        SELECT u.id, u.email, u.role, u.status,
               CASE WHEN r.id IS NOT NULL THEN 'YES' ELSE 'NO' END as has_resident,
               CASE WHEN o.id IS NOT NULL THEN 'YES' ELSE 'NO' END as has_owner,
               COALESCE(r.erf_number, o.erf_number) as erf_number
        FROM users u 
        LEFT JOIN residents r ON u.id = r.user_id 
        LEFT JOIN owners o ON u.id = o.user_id 
        WHERE u.email = 'johanvonlandsberg080808@gmai.com'
    """)
    
    fixed_data = cursor.fetchall()
    for data in fixed_data:
        print(f"  User: {data[1]}, Role: {data[2]}, Resident: {data[4]}, Owner: {data[5]}, ERF: {data[6]}")
    
    conn.close()
    
    print("\n🎉 Login issues should now be resolved!")
    print("   Try logging in with: johanvonlandsberg080808@gmai.com")

if __name__ == "__main__":
    fix_login_issues()
