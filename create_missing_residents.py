#!/usr/bin/env python3
"""
Fix login issues with correct database schema.
"""

import sqlite3
import uuid
from datetime import datetime

def fix_resident_records():
    """Create missing resident records with correct schema"""
    
    db_path = "altona_village_cms/src/database/app.db"
    
    print("🔧 Creating Missing Resident Records")
    print("=" * 50)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get users with resident role but no resident records
    cursor.execute("""
        SELECT u.id, u.email, o.first_name, o.last_name, o.phone_number, 
               o.id_number, o.erf_number, o.street_number, o.street_name, o.full_address
        FROM users u 
        JOIN owners o ON u.id = o.user_id 
        WHERE u.role = 'resident' 
        AND u.id NOT IN (SELECT user_id FROM residents WHERE user_id IS NOT NULL)
        AND u.email = 'johanvonlandsberg080808@gmai.com'
    """)
    
    missing_residents = cursor.fetchall()
    
    print(f"👥 Found {len(missing_residents)} users needing resident records:")
    
    for user_data in missing_residents:
        user_id = user_data[0]
        email = user_data[1]
        first_name = user_data[2]
        last_name = user_data[3]
        phone = user_data[4]
        id_number = user_data[5]
        erf_number = user_data[6]
        street_number = user_data[7]
        street_name = user_data[8]
        full_address = user_data[9]
        
        print(f"  Creating resident for {email} - ERF {erf_number}")
        
        # Create resident record using correct schema
        resident_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        insert_sql = """
            INSERT INTO residents (
                id, user_id, first_name, last_name, phone_number, 
                id_number, erf_number, street_number, street_name, full_address,
                intercom_code, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            cursor.execute(insert_sql, (
                resident_id, user_id, first_name, last_name, phone,
                id_number, erf_number, street_number, street_name, full_address,
                '1234', 'active', now, now
            ))
            
            print(f"  ✅ Created resident record for ERF {erf_number}")
            
        except sqlite3.Error as e:
            print(f"  ❌ Error creating resident for ERF {erf_number}: {e}")
    
    conn.commit()
    
    # Verify the fix
    print("\n✅ Verification:")
    cursor.execute("""
        SELECT u.email, u.role,
               COUNT(DISTINCT r.id) as resident_count,
               COUNT(DISTINCT o.id) as owner_count,
               GROUP_CONCAT(DISTINCT r.erf_number) as resident_erfs,
               GROUP_CONCAT(DISTINCT o.erf_number) as owner_erfs
        FROM users u 
        LEFT JOIN residents r ON u.id = r.user_id 
        LEFT JOIN owners o ON u.id = o.user_id 
        WHERE u.email = 'johanvonlandsberg080808@gmai.com'
        GROUP BY u.email, u.role
    """)
    
    verification = cursor.fetchall()
    for v in verification:
        print(f"  {v[0]} - Role: {v[1]}")
        print(f"    Resident Records: {v[2]} (ERFs: {v[4] or 'None'})")
        print(f"    Owner Records: {v[3]} (ERFs: {v[5] or 'None'})")
    
    conn.close()
    
    print("\n🎉 Resident records created! Login should now work.")

if __name__ == "__main__":
    fix_resident_records()
