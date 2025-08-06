#!/usr/bin/env python3
"""
Debug Vehicle Display Issue
Test the vehicle retrieval API to see why vehicles aren't showing on the user interface
"""

import requests
import json
import sys

def test_vehicle_retrieval():
    """Test the vehicle retrieval API"""
    
    frontend_url = "http://localhost:5173"
    backend_url = "http://localhost:5000"
    
    print("🔍 DEBUGGING VEHICLE DISPLAY ISSUE")
    print("=" * 60)
    
    # Test login first
    print("\n1. Testing login...")
    login_data = {
        "email": "hi@hi1",
        "password": "test"
    }
    
    try:
        # Login via frontend proxy
        login_response = requests.post(f"{frontend_url}/api/auth/login", json=login_data)
        print(f"   Login Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get('access_token')
            user_data = login_result.get('user', {})
            print(f"   Login Success: {user_data.get('email')}")
            print(f"   User ID: {user_data.get('id')}")
            print(f"   User Role: {user_data.get('role')}")
            
            if token:
                print(f"   Token obtained: {token[:20]}...")
                
                # Test vehicle retrieval via frontend proxy
                print("\n2. Testing vehicle retrieval via frontend proxy...")
                headers = {"Authorization": f"Bearer {token}"}
                
                vehicles_response = requests.get(f"{frontend_url}/api/resident/vehicles", headers=headers)
                print(f"   Vehicle API Status: {vehicles_response.status_code}")
                
                if vehicles_response.status_code == 200:
                    vehicles = vehicles_response.json()
                    print(f"   Vehicles Retrieved: {len(vehicles)}")
                    
                    if vehicles:
                        print("\n   📋 VEHICLES FOUND:")
                        for i, vehicle in enumerate(vehicles, 1):
                            print(f"      {i}. {vehicle.get('registration_number')} - {vehicle.get('make')} {vehicle.get('model')}")
                            print(f"         ERF: {vehicle.get('erf_number')}")
                            print(f"         User ID: {vehicle.get('user_id')}")
                            print(f"         Status: {vehicle.get('status', 'No status')}")
                            print(f"         Owner ID: {vehicle.get('owner_id', 'None')}")
                            print(f"         Resident ID: {vehicle.get('resident_id', 'None')}")
                    else:
                        print("   ⚠️ NO VEHICLES FOUND - This is the issue!")
                        
                        # Let's check direct backend
                        print("\n3. Testing direct backend...")
                        backend_vehicles_response = requests.get(f"{backend_url}/api/resident/vehicles", headers=headers)
                        print(f"   Backend API Status: {backend_vehicles_response.status_code}")
                        
                        if backend_vehicles_response.status_code == 200:
                            backend_vehicles = backend_vehicles_response.json()
                            print(f"   Backend Vehicles: {len(backend_vehicles)}")
                            
                            if backend_vehicles:
                                print("   🚗 BACKEND HAS VEHICLES:")
                                for vehicle in backend_vehicles:
                                    print(f"      - {vehicle.get('registration_number')}")
                        else:
                            print(f"   Backend Error: {backend_vehicles_response.text}")
                            
                else:
                    print(f"   Vehicle API Error: {vehicles_response.text}")
                    
                # Test database directly
                print("\n4. Testing database directly...")
                test_database_vehicles(user_data.get('email'))
                
            else:
                print("   ❌ No token in login response")
        else:
            print(f"   Login Failed: {login_response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_database_vehicles(email):
    """Check vehicles directly in database"""
    import sqlite3
    import os
    
    try:
        db_path = os.path.join('altona_village_cms', 'src', 'database', 'app.db')
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get user accounts for this email
            cursor.execute("SELECT id, email, role FROM users WHERE email = ?", (email,))
            users = cursor.fetchall()
            
            print(f"   User accounts found: {len(users)}")
            for user in users:
                print(f"      - User ID: {user[0]}, Role: {user[2]}")
            
            # Get all vehicles
            cursor.execute("SELECT * FROM vehicles")
            all_vehicles = cursor.fetchall()
            print(f"   Total vehicles in database: {len(all_vehicles)}")
            
            if all_vehicles:
                print("   🚗 ALL VEHICLES IN DATABASE:")
                cursor.execute("PRAGMA table_info(vehicles)")
                columns = [column[1] for column in cursor.fetchall()]
                
                for vehicle in all_vehicles:
                    vehicle_dict = dict(zip(columns, vehicle))
                    print(f"      - {vehicle_dict.get('registration_number')}")
                    print(f"        Resident ID: {vehicle_dict.get('resident_id')}")
                    print(f"        Owner ID: {vehicle_dict.get('owner_id')}")
                    print(f"        Status: {vehicle_dict.get('status')}")
                    
            # Check residents table
            cursor.execute("SELECT id, user_id, erf_number FROM residents")
            residents = cursor.fetchall()
            print(f"   Residents in database: {len(residents)}")
            for resident in residents:
                print(f"      - Resident ID: {resident[0]}, User ID: {resident[1]}, ERF: {resident[2]}")
            
            # Check owners table
            cursor.execute("SELECT id, user_id, erf_number FROM owners")
            owners = cursor.fetchall()
            print(f"   Owners in database: {len(owners)}")
            for owner in owners:
                print(f"      - Owner ID: {owner[0]}, User ID: {owner[1]}, ERF: {owner[2]}")
            
            conn.close()
        else:
            print(f"   ❌ Database not found at: {db_path}")
            
    except Exception as e:
        print(f"   ❌ Database error: {e}")

if __name__ == "__main__":
    test_vehicle_retrieval()
