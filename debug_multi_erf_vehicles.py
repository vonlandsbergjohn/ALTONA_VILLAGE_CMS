#!/usr/bin/env python3
"""
Debug Multi-ERF User Vehicle Display
Check how multi-ERF users are handled in vehicle retrieval
"""

import sqlite3
import os
import requests

def check_multi_erf_users():
    """Check multi-ERF user setup and vehicle assignments"""
    
    db_path = os.path.join('altona_village_cms', 'src', 'database', 'app.db')
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 MULTI-ERF USER ANALYSIS")
    print("=" * 60)
    
    # Check all users and their ERF associations
    cursor.execute("""
        SELECT DISTINCT u.email, u.role, 
               r.erf_number as resident_erf, r.id as resident_id,
               o.erf_number as owner_erf, o.id as owner_id
        FROM users u
        LEFT JOIN residents r ON u.id = r.user_id
        LEFT JOIN owners o ON u.id = o.user_id
        WHERE u.email LIKE '%johann%' OR u.email = 'hi@hi1'
        ORDER BY u.email
    """)
    
    users = cursor.fetchall()
    
    print("\n👥 USERS AND THEIR ERF ASSOCIATIONS:")
    for user in users:
        email, role, resident_erf, resident_id, owner_erf, owner_id = user
        print(f"\n📧 {email} ({role})")
        if resident_erf:
            print(f"   🏠 Resident ERF: {resident_erf} (ID: {resident_id})")
        if owner_erf:
            print(f"   🏡 Owner ERF: {owner_erf} (ID: {owner_id})")
        
        # Check vehicles for this user
        cursor.execute("""
            SELECT registration_number, make, model, resident_id, owner_id, status
            FROM vehicles 
            WHERE resident_id = ? OR owner_id = ?
        """, (resident_id, owner_id))
        
        vehicles = cursor.fetchall()
        if vehicles:
            print(f"   🚗 Vehicles ({len(vehicles)}):")
            for vehicle in vehicles:
                reg, make, model, v_resident_id, v_owner_id, status = vehicle
                print(f"      - {reg} ({make} {model}) - Resident: {v_resident_id}, Owner: {v_owner_id}, Status: {status}")
        else:
            print(f"   🚗 No vehicles found")
    
    # Check if there are multiple user accounts with same email
    print("\n📊 EMAIL DUPLICATION CHECK:")
    cursor.execute("""
        SELECT email, COUNT(*) as account_count
        FROM users 
        GROUP BY email
        HAVING COUNT(*) > 1
    """)
    
    duplicate_emails = cursor.fetchall()
    if duplicate_emails:
        print("   Found users with multiple accounts:")
        for email, count in duplicate_emails:
            print(f"      {email}: {count} accounts")
            
            # Show all accounts for this email
            cursor.execute("SELECT id, role FROM users WHERE email = ?", (email,))
            accounts = cursor.fetchall()
            for account in accounts:
                user_id, role = account
                print(f"         - User ID: {user_id}, Role: {role}")
    else:
        print("   No duplicate emails found")
    
    conn.close()

def test_multi_erf_api():
    """Test the vehicle API with multi-ERF user"""
    
    print("\n🔍 TESTING MULTI-ERF API")
    print("=" * 60)
    
    frontend_url = "http://localhost:5173"
    
    # Test the multi-ERF user from the screenshot
    test_email = "johannvonlandsberg080808@gmail.com"
    test_password = "testpassword123"  # Try common test password
    
    print(f"\n👤 Testing: {test_email}")
    
    try:
        # Login
        login_response = requests.post(f"{frontend_url}/api/auth/login", json={
            "email": test_email,
            "password": test_password
        })
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get('access_token')
            user_info = login_result.get('user', {})
            
            print(f"   ✅ Login Success")
            print(f"   User ID: {user_info.get('id')}")
            print(f"   Role: {user_info.get('role')}")
            print(f"   Email: {user_info.get('email')}")
            
            if token:
                headers = {"Authorization": f"Bearer {token}"}
                
                # Test vehicle retrieval
                print("\n🚗 Testing vehicle retrieval...")
                vehicles_response = requests.get(f"{frontend_url}/api/resident/vehicles", headers=headers)
                print(f"   Status: {vehicles_response.status_code}")
                
                if vehicles_response.status_code == 200:
                    vehicles = vehicles_response.json()
                    print(f"   Vehicle Count: {len(vehicles)}")
                    
                    if vehicles:
                        print("   Vehicles Found:")
                        for i, vehicle in enumerate(vehicles, 1):
                            print(f"      {i}. {vehicle.get('registration_number')} - {vehicle.get('make')} {vehicle.get('model')}")
                            print(f"         ERF: {vehicle.get('erf_number')}")
                            print(f"         User ID: {vehicle.get('user_id')}")
                    else:
                        print("   ❌ No vehicles returned - This is the multi-ERF issue!")
                        
                        # Let's check what user accounts exist for this email
                        print("\n🔍 Checking user accounts for this email...")
                        check_user_accounts_by_email(test_email)
                        
                else:
                    print(f"   Error: {vehicles_response.text}")
                    
                # Test properties
                properties_response = requests.get(f"{frontend_url}/api/resident/properties", headers=headers)
                if properties_response.status_code == 200:
                    properties = properties_response.json()
                    print(f"   Property Count: {len(properties)}")
        
        else:
            print(f"   ❌ Login Failed: {login_response.status_code}")
            # Try other common passwords
            for alt_password in ["password123", "test", "admin"]:
                print(f"   Trying password: {alt_password}")
                alt_response = requests.post(f"{frontend_url}/api/auth/login", json={
                    "email": test_email,
                    "password": alt_password
                })
                if alt_response.status_code == 200:
                    print(f"   ✅ Success with password: {alt_password}")
                    break
                    
    except Exception as e:
        print(f"   ❌ Error: {e}")

def check_user_accounts_by_email(email):
    """Check all user accounts for a specific email"""
    
    db_path = os.path.join('altona_village_cms', 'src', 'database', 'app.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT u.id, u.email, u.role, u.status,
               r.id as resident_id, r.erf_number as resident_erf,
               o.id as owner_id, o.erf_number as owner_erf
        FROM users u
        LEFT JOIN residents r ON u.id = r.user_id
        LEFT JOIN owners o ON u.id = o.user_id
        WHERE u.email = ?
    """, (email,))
    
    accounts = cursor.fetchall()
    
    print(f"      Found {len(accounts)} account(s) for {email}:")
    for account in accounts:
        user_id, email, role, status, resident_id, resident_erf, owner_id, owner_erf = account
        print(f"         - User: {user_id} ({role}, {status})")
        if resident_id:
            print(f"           Resident: {resident_id} (ERF {resident_erf})")
        if owner_id:
            print(f"           Owner: {owner_id} (ERF {owner_erf})")
            
        # Check vehicles for each account
        cursor.execute("""
            SELECT COUNT(*) FROM vehicles 
            WHERE resident_id = ? OR owner_id = ?
        """, (resident_id, owner_id))
        vehicle_count = cursor.fetchone()[0]
        print(f"           Vehicles: {vehicle_count}")
    
    conn.close()

if __name__ == "__main__":
    check_multi_erf_users()
    test_multi_erf_api()
