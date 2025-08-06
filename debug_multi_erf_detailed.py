#!/usr/bin/env python3
"""
Fix Multi-ERF Vehicle Retrieval Issue
Create proper test multi-ERF user and check the API logic
"""

import sqlite3
import os
import requests

def check_multi_erf_logic():
    """Check the multi-ERF logic in detail"""
    
    db_path = os.path.join('altona_village_cms', 'src', 'database', 'app.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 DETAILED MULTI-ERF ANALYSIS")
    print("=" * 60)
    
    # Check the user with multiple accounts
    email = "johanvonlandsberg080808@gmail.com"
    
    print(f"\n👤 Analyzing: {email}")
    
    cursor.execute("""
        SELECT u.id, u.email, u.role, u.status,
               r.id as resident_id, r.first_name, r.last_name, r.erf_number as resident_erf,
               o.id as owner_id, o.first_name as owner_first, o.last_name as owner_last, o.erf_number as owner_erf
        FROM users u
        LEFT JOIN residents r ON u.id = r.user_id
        LEFT JOIN owners o ON u.id = o.user_id
        WHERE u.email = ?
        ORDER BY u.id
    """, (email,))
    
    accounts = cursor.fetchall()
    
    print(f"\n📋 USER ACCOUNTS ({len(accounts)}):")
    all_resident_ids = []
    all_owner_ids = []
    
    for i, account in enumerate(accounts, 1):
        user_id, email, role, status, resident_id, r_first, r_last, resident_erf, owner_id, o_first, o_last, owner_erf = account
        print(f"\n   Account {i}: {user_id}")
        print(f"      Role: {role}, Status: {status}")
        
        if resident_id:
            print(f"      🏠 Resident: {r_first} {r_last} (ERF {resident_erf})")
            all_resident_ids.append(resident_id)
        
        if owner_id:
            print(f"      🏡 Owner: {o_first} {o_last} (ERF {owner_erf})")
            all_owner_ids.append(owner_id)
    
    # Check vehicles for all resident/owner IDs
    print(f"\n🚗 VEHICLE SEARCH:")
    print(f"   Searching for resident IDs: {all_resident_ids}")
    print(f"   Searching for owner IDs: {all_owner_ids}")
    
    all_vehicles = []
    
    # Search by resident IDs
    for resident_id in all_resident_ids:
        cursor.execute("""
            SELECT id, registration_number, make, model, resident_id, owner_id, status
            FROM vehicles WHERE resident_id = ?
        """, (resident_id,))
        vehicles = cursor.fetchall()
        all_vehicles.extend(vehicles)
        print(f"   Resident {resident_id}: {len(vehicles)} vehicles")
    
    # Search by owner IDs
    for owner_id in all_owner_ids:
        cursor.execute("""
            SELECT id, registration_number, make, model, resident_id, owner_id, status
            FROM vehicles WHERE owner_id = ?
        """, (owner_id,))
        vehicles = cursor.fetchall()
        all_vehicles.extend(vehicles)
        print(f"   Owner {owner_id}: {len(vehicles)} vehicles")
    
    # Remove duplicates
    unique_vehicles = []
    seen_ids = set()
    for vehicle in all_vehicles:
        if vehicle[0] not in seen_ids:  # vehicle[0] is the ID
            unique_vehicles.append(vehicle)
            seen_ids.add(vehicle[0])
    
    print(f"\n   📊 Total unique vehicles: {len(unique_vehicles)}")
    
    if unique_vehicles:
        print("   🚗 Vehicles found:")
        for vehicle in unique_vehicles:
            vid, reg, make, model, res_id, own_id, status = vehicle
            print(f"      - {reg} ({make} {model}) - Resident: {res_id}, Owner: {own_id}")
    
    # Now simulate the API logic
    print(f"\n🔧 SIMULATING API LOGIC:")
    
    cursor.execute("SELECT id FROM users WHERE email = ? LIMIT 1", (email,))
    current_user_result = cursor.fetchone()
    
    if current_user_result:
        current_user_id = current_user_result[0]
        print(f"   Current user ID: {current_user_id}")
        
        # Simulate the API's "get all user accounts with same email"
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        all_user_accounts = cursor.fetchall()
        print(f"   Found {len(all_user_accounts)} accounts with same email")
        
        vehicles_from_api_logic = []
        seen_vehicle_ids = set()
        
        for user_account_row in all_user_accounts:
            user_account_id = user_account_row[0]
            print(f"\n   Processing account: {user_account_id}")
            
            # Check if this account has a resident record
            cursor.execute("SELECT id, erf_number FROM residents WHERE user_id = ?", (user_account_id,))
            resident = cursor.fetchone()
            
            if resident:
                resident_id, erf = resident
                print(f"      Has resident: {resident_id} (ERF {erf})")
                
                cursor.execute("""
                    SELECT id, registration_number, make, model 
                    FROM vehicles WHERE resident_id = ?
                """, (resident_id,))
                resident_vehicles = cursor.fetchall()
                
                for vehicle in resident_vehicles:
                    if vehicle[0] not in seen_vehicle_ids:
                        vehicles_from_api_logic.append(vehicle)
                        seen_vehicle_ids.add(vehicle[0])
                        print(f"         Found vehicle: {vehicle[1]}")
            
            # Check if this account has an owner record
            cursor.execute("SELECT id, erf_number FROM owners WHERE user_id = ?", (user_account_id,))
            owner = cursor.fetchone()
            
            if owner:
                owner_id, erf = owner
                print(f"      Has owner: {owner_id} (ERF {erf})")
                
                cursor.execute("""
                    SELECT id, registration_number, make, model 
                    FROM vehicles WHERE owner_id = ?
                """, (owner_id,))
                owner_vehicles = cursor.fetchall()
                
                for vehicle in owner_vehicles:
                    if vehicle[0] not in seen_vehicle_ids:
                        vehicles_from_api_logic.append(vehicle)
                        seen_vehicle_ids.add(vehicle[0])
                        print(f"         Found vehicle: {vehicle[1]}")
        
        print(f"\n   📊 API would return: {len(vehicles_from_api_logic)} vehicles")
        
        if len(vehicles_from_api_logic) != len(unique_vehicles):
            print(f"   ❌ MISMATCH! Expected {len(unique_vehicles)}, API returns {len(vehicles_from_api_logic)}")
        else:
            print(f"   ✅ API logic is working correctly")
    
    conn.close()

def create_test_multi_erf_user():
    """Create a proper test user with multiple ERFs for testing"""
    
    db_path = os.path.join('altona_village_cms', 'src', 'database', 'app.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🔧 CREATING TEST MULTI-ERF USER")
    print("=" * 60)
    
    # Create a test user with vehicles on multiple ERFs
    test_email = "multierf@test.com"
    
    # First, check if user already exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (test_email,))
    if cursor.fetchone():
        print(f"   User {test_email} already exists, skipping creation")
        conn.close()
        return
    
    import uuid
    from datetime import datetime
    
    # Create first account (ERF 27681 - Owner)
    user_id_1 = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO users (id, email, password_hash, role, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id_1, test_email, "$2b$12$dummy.hash.for.testing", "owner", "active", datetime.now()))
    
    owner_id_1 = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO owners (id, user_id, first_name, last_name, phone_number, id_number, erf_number, 
                           street_number, street_name, full_address, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (owner_id_1, user_id_1, "Multi", "ERF Owner", "+27123456789", "1234567890", "27681",
          "10", "Test Street", "10 Test Street", "active", datetime.now(), datetime.now()))
    
    # Create second account (ERF 27683 - Resident)
    user_id_2 = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO users (id, email, password_hash, role, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id_2, test_email, "$2b$12$dummy.hash.for.testing", "resident", "active", datetime.now()))
    
    resident_id_2 = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO residents (id, user_id, first_name, last_name, phone_number, id_number, erf_number,
                              street_number, street_name, full_address, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (resident_id_2, user_id_2, "Multi", "ERF Resident", "+27123456789", "1234567890", "27683",
          "15", "Another Street", "15 Another Street", "active", datetime.now(), datetime.now()))
    
    # Add vehicles to both accounts
    vehicle_id_1 = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO vehicles (id, registration_number, make, model, year, color, vehicle_type, 
                             owner_id, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (vehicle_id_1, "MULTI1GP", "Toyota", "Camry", 2020, "White", "car",
          owner_id_1, "active", datetime.now(), datetime.now()))
    
    vehicle_id_2 = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO vehicles (id, registration_number, make, model, year, color, vehicle_type,
                             resident_id, owner_id, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (vehicle_id_2, "MULTI2GP", "Honda", "Civic", 2021, "Blue", "car",
          resident_id_2, None, "active", datetime.now(), datetime.now()))
    
    conn.commit()
    conn.close()
    
    print(f"   ✅ Created test user: {test_email}")
    print(f"      Account 1: {user_id_1} (Owner, ERF 27681) - Vehicle: MULTI1GP")
    print(f"      Account 2: {user_id_2} (Resident, ERF 27683) - Vehicle: MULTI2GP")

if __name__ == "__main__":
    check_multi_erf_logic()
    create_test_multi_erf_user()
