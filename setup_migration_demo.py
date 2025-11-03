#!/usr/bin/env python3
"""
Simple Test Setup for User Migration Demo
Creates a basic scenario to test the password handling functionality
"""

import psycopg2
import os
from datetime import datetime
import uuid
from werkzeug.security import generate_password_hash

DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://postgres:%23Johnvonl1977@localhost:5432/altona_village_db")

def setup_demo_scenario():
    """Create a simple test scenario for migration demo"""
    print("🎯 SETTING UP DEMO MIGRATION SCENARIO")
    print("=" * 50)
    
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # Test Scenario: Owner wants to become owner-resident (moves into property)
        # This tests SCENARIO 2: Same person, password should be preserved
        
        # Create test owner
        user_id = str(uuid.uuid4())
        user_email = "john.owner@demo.com"
        password_hash = generate_password_hash('demo123')
        
        cursor.execute("""
            INSERT INTO users (id, email, password_hash, role, status, created_at, updated_at)
            VALUES (%s, %s, %s, 'owner', 'active', %s, %s)
        """, (user_id, user_email, password_hash, datetime.now(), datetime.now()))
        
        # Create owner record
        owner_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO owners (id, user_id, first_name, last_name, erf_number, phone_number, 
                              id_number, street_number, street_name, full_address, intercom_code, 
                              title_deed_number, postal_street_number, postal_street_name, 
                              postal_suburb, postal_city, postal_code, postal_province, 
                              full_postal_address, status, created_at, updated_at)
            VALUES (%s, %s, 'John', 'Owner', '1001', '123456789', '8001010001080', '1', 'Main Street',
                   '1 Main Street, ERF 1001', '1001', 'T001001', '1', 'Main Street', 'Suburb',
                   'City', '0001', 'Province', '1 Main Street, Suburb, City, 0001', 'active', %s, %s)
        """, (owner_id, user_id, datetime.now(), datetime.now()))
        
        print(f"✅ Created test user: {user_email}")
        print(f"   Role: Owner at ERF 1001")
        print(f"   Password: demo123")
        
        # Create transition request: Owner becomes owner-resident
        req_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO user_transition_requests 
            (id, user_id, erf_number, request_type, current_role, new_occupant_type,
             new_occupant_first_name, new_occupant_last_name, new_occupant_email,
             status, priority, created_at, updated_at)
            VALUES (%s, %s, '1001', 'owner_moving', 'owner', 'owner_resident',
                   'John', 'Owner', ?, 'pending_review', 'standard', ?, ?)
        """, (req_id, user_id, user_email, datetime.now(), datetime.now()))
        
        print(f"✅ Created transition request: {req_id}")
        print(f"   Type: Owner → Owner-Resident (same person)")
        
        conn.commit()
        
        return {
            'user_id': user_id,
            'user_email': user_email,
            'request_id': req_id,
            'erf': '1001',
            'scenario': 'role_change'
        }
        
    except Exception as e:
        print(f"❌ Error setting up demo: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()

def show_demo_instructions(demo_data):
    """Show instructions for testing the migration"""
    print("\n🚀 DEMO READY - TEST INSTRUCTIONS")
    print("=" * 50)
    print("1. Open your browser to: http://localhost:5173/")
    print("2. Login as admin")
    print("3. Go to: Admin → Transition Requests")
    print(f"4. Find request for ERF {demo_data['erf']} (John Owner)")
    print("5. Click on the request to view details")
    print("6. Change status from 'pending_review' to 'completed'")
    print("7. Save the status change")
    print()
    print("🔍 WHAT TO OBSERVE:")
    print("• Migration should detect: SAME PERSON (same email)")
    print("• User password should be PRESERVED (not disabled)")
    print("• User role should change from 'owner' to 'owner_resident'")
    print(f"• New resident record should be created for ERF {demo_data['erf']}")
    print("• Existing owner record should remain active")
    print()
    print("📊 VERIFICATION:")
    print("• Check backend terminal for migration logs")
    print("• User should still be able to login with: demo123")
    print("• Gate Register should show both owner and resident roles")
    
def verify_current_state():
    """Show current state before migration"""
    print("\n📋 CURRENT STATE BEFORE MIGRATION")
    print("=" * 50)
    
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT u.email, u.role, u.status, 
                   CASE WHEN u.password_hash = 'DISABLED' THEN 'DISABLED' ELSE 'ACTIVE' END as password_status
            FROM users u WHERE u.email LIKE '%%demo.com'
        """)
        users = cursor.fetchall()
        
        print("👥 USERS:")
        for email, role, status, pwd_status in users:
            print(f"   {email:<25} | {role:<15} | {status:<10} | Password: {pwd_status}")
        
        cursor.execute("""
            SELECT r.first_name, r.last_name, r.erf_number, r.status
            FROM residents r JOIN users u ON r.user_id = u.id
            WHERE u.email LIKE '%%demo.com'
        """)
        residents = cursor.fetchall()
        
        print("\n🏠 RESIDENTS:")
        if residents:
            for fname, lname, erf, status in residents:
                print(f"   ERF {erf} | {fname} {lname} | Status: {status}")
        else:
            print("   None (will be created during migration)")
        
        cursor.execute("""
            SELECT o.first_name, o.last_name, o.erf_number, o.status
            FROM owners o JOIN users u ON o.user_id = u.id
            WHERE u.email LIKE '%%demo.com'
        """)
        owners = cursor.fetchall()
        
        print("\n🏢 OWNERS:")
        for fname, lname, erf, status in owners:
            print(f"   ERF {erf} | {fname} {lname} | Status: {status}")
        
    except Exception as e:
        print(f"❌ Error checking state: {e}")
    finally:
        if conn:
            conn.close()

def main():
    print("🧪 USER MIGRATION DEMO SETUP")
    print("Testing: SCENARIO 2 - Role Change (Password Preservation)")
    print()
    
    # Setup demo scenario
    demo_data = setup_demo_scenario()
    if not demo_data:
        print("❌ Demo setup failed")
        return False
    
    # Show current state
    verify_current_state()
    
    # Show test instructions
    show_demo_instructions(demo_data)
    
    print("\n✅ DEMO SETUP COMPLETE!")
    print("\nReady to test the migration system! 🚀")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
