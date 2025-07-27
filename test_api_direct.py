#!/usr/bin/env python3

"""
Test API endpoints directly to debug issues
"""

import requests
import json
import sys
import os

# Add the project directory to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_api():
    base_url = "http://localhost:5000/api"
    
    # Test login first to get token
    print("=== Testing Login ===")
    login_data = {
        "email": "vonlandsbergjohn@gmail.com",
        "password": "admin123"  # Update with actual password
    }
    
    try:
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        print(f"Login response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print(f"Login successful! Token: {token[:20]}...")
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test gate register
            print("\n=== Testing Gate Register ===")
            gate_response = requests.get(f"{base_url}/gate-register", headers=headers)
            print(f"Gate register response: {gate_response.status_code}")
            
            if gate_response.status_code == 200:
                gate_data = gate_response.json()
                print(f"Gate register data: {json.dumps(gate_data, indent=2)}")
            else:
                print(f"Gate register error: {gate_response.text}")
            
            # Test admin users
            print("\n=== Testing Admin Users ===")
            users_response = requests.get(f"{base_url}/admin/users", headers=headers)
            print(f"Users response: {users_response.status_code}")
            
            if users_response.status_code == 200:
                users_data = users_response.json()
                print(f"Found {len(users_data)} users")
                for user in users_data[:2]:  # Show first 2 users
                    print(f"  User: {user.get('email')} - {user.get('role')} - {user.get('status')}")
                    if user.get('id'):
                        # Test getting vehicles for this user
                        print(f"\n    Testing vehicles for user {user.get('email')}:")
                        vehicles_response = requests.get(f"{base_url}/admin/residents/{user['id']}/vehicles", headers=headers)
                        print(f"    Vehicles response: {vehicles_response.status_code}")
                        if vehicles_response.status_code == 200:
                            vehicles = vehicles_response.json()
                            print(f"    Found {len(vehicles)} vehicles: {[v.get('registration_number') for v in vehicles]}")
                        else:
                            print(f"    Vehicles error: {vehicles_response.text}")
            else:
                print(f"Users error: {users_response.text}")
        else:
            print(f"Login failed: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
