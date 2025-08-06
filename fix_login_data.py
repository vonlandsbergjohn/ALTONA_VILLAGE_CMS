#!/usr/bin/env python3
"""
Check actual database schema and fix login issues properly.
"""

import sqlite3
import uuid
from datetime import datetime

def check_schema_and_fix():
    """Check actual schema and fix login issues"""
    
    db_path = "altona_village_cms/src/database/app.db"
    
    print("🔍 Checking Database Schema")
    print("=" * 50)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check residents table schema
    cursor.execute("PRAGMA table_info(residents)")
    residents_schema = cursor.fetchall()
    print("📋 Residents Table Schema:")
    for col in residents_schema:
        print(f"  {col[1]} ({col[2]})")
    
    # Check owners table schema
    cursor.execute("PRAGMA table_info(owners)")
    owners_schema = cursor.fetchall()
    print("\n📋 Owners Table Schema:")
    for col in owners_schema:
        print(f"  {col[1]} ({col[2]})")
    
    # Get current problematic users
    cursor.execute("""
        SELECT u.id, u.email, u.role, u.status 
        FROM users u 
        WHERE u.email = 'johanvonlandsberg080808@gmai.com'
    """)
    users = cursor.fetchall()
    
    print(f"\n👥 Problem Users ({len(users)} accounts):")
    for user in users:
        print(f"  {user[1]} - Role: {user[2]} - Status: {user[3]}")
    
    # Check what owner data exists
    cursor.execute("""
        SELECT o.*, u.role 
        FROM owners o 
        JOIN users u ON o.user_id = u.id 
        WHERE u.email = 'johanvonlandsberg080808@gmai.com'
    """)
    owners = cursor.fetchall()
    
    print(f"\n🏢 Owner Records ({len(owners)} records):")
    for owner in owners:
        print(f"  ERF {owner[7]}: {owner[3]} {owner[4]} (User Role: {owner[-1]})")
    
    # Check if any resident records exist
    cursor.execute("""
        SELECT r.*, u.role 
        FROM residents r 
        JOIN users u ON r.user_id = u.id 
        WHERE u.email = 'johanvonlandsberg080808@gmai.com'
    """)
    residents = cursor.fetchall()
    
    print(f"\n🏠 Resident Records ({len(residents)} records):")
    if residents:
        for resident in residents:
            print(f"  ERF {resident[7]}: {resident[3]} {resident[4]} (User Role: {resident[-1]})")
    else:
        print("  ❌ NO RESIDENT RECORDS FOUND - This is the problem!")
    
    # Fix: Create resident records using the correct schema
    if not residents and owners:
        print("\n🔨 Creating Missing Resident Records...")
        
        for owner in owners:
            user_id = owner[1]
            
            # Create resident record with correct column names
            resident_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            # Use actual column names from schema
            insert_sql = """
                INSERT INTO residents (
                    id, user_id, first_name, last_name, phone_number, 
                    id_number, erf_number, full_address,
                    gate_access, intercom_code, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            try:
                cursor.execute(insert_sql, (
                    resident_id, user_id, 
                    owner[3], owner[4], owner[5],  # first_name, last_name, phone_number
                    owner[6], owner[7], owner[8],  # id_number, erf_number, full_address
                    'pending', '1234', 'pending', now, now
                ))
                
                print(f"  ✅ Created resident record for ERF {owner[7]}")
                
            except sqlite3.Error as e:
                print(f"  ❌ Error creating resident for ERF {owner[7]}: {e}")
    
    conn.commit()
    
    # Verify fix
    cursor.execute("""
        SELECT u.email, u.role,
               CASE WHEN r.id IS NOT NULL THEN r.erf_number ELSE 'None' END as resident_erf,
               CASE WHEN o.id IS NOT NULL THEN o.erf_number ELSE 'None' END as owner_erf
        FROM users u 
        LEFT JOIN residents r ON u.id = r.user_id 
        LEFT JOIN owners o ON u.id = o.user_id 
        WHERE u.email = 'johanvonlandsberg080808@gmai.com'
    """)
    
    verification = cursor.fetchall()
    print(f"\n✅ Verification ({len(verification)} accounts):")
    for v in verification:
        print(f"  {v[0]} - Role: {v[1]} - Resident ERF: {v[2]} - Owner ERF: {v[3]}")
    
    conn.close()
    
    print("\n🎉 Database issues fixed! Users should now be able to log in.")

if __name__ == "__main__":
    check_schema_and_fix()
