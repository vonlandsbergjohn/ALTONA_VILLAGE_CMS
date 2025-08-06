#!/usr/bin/env python3
"""
Debug Frontend API Response Structure
"""

import requests
import json

def debug_frontend_api():
    base_url = 'http://localhost:5000'
    
    print("🔍 DEBUGGING FRONTEND API RESPONSE STRUCTURE")
    print("=" * 50)
    
    # Login first
    login_url = f'{base_url}/api/auth/login'
    login_data = {
        'email': 'johanvonlandsberg080808@gmail.com',
        'password': 'test'
    }
    
    try:
        login_response = requests.post(login_url, json=login_data, timeout=10)
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get('access_token')
            user_info = login_result.get('user', {})
            
            print(f"✅ Logged in as: {user_info.get('email')}")
            print(f"   User ID: {user_info.get('id')}")
            
            # Test all the dashboard APIs
            headers = {'Authorization': f'Bearer {token}'}
            
            # Test vehicles API
            print(f"\n🚗 VEHICLES API:")
            vehicles_url = f'{base_url}/api/resident/vehicles'
            vehicles_response = requests.get(vehicles_url, headers=headers, timeout=10)
            print(f"   Status: {vehicles_response.status_code}")
            
            if vehicles_response.status_code == 200:
                vehicles_data = vehicles_response.json()
                print(f"   Type: {type(vehicles_data)}")
                print(f"   Is Array: {isinstance(vehicles_data, list)}")
                print(f"   Length: {len(vehicles_data) if isinstance(vehicles_data, list) else 'N/A'}")
                print(f"   Sample: {vehicles_data[:1] if isinstance(vehicles_data, list) and vehicles_data else vehicles_data}")
            
            # Test complaints API
            print(f"\n📋 COMPLAINTS API:")
            complaints_url = f'{base_url}/api/resident/complaints'
            complaints_response = requests.get(complaints_url, headers=headers, timeout=10)
            print(f"   Status: {complaints_response.status_code}")
            
            if complaints_response.status_code == 200:
                complaints_data = complaints_response.json()
                print(f"   Type: {type(complaints_data)}")
                print(f"   Is Array: {isinstance(complaints_data, list)}")
                print(f"   Length: {len(complaints_data) if isinstance(complaints_data, list) else 'N/A'}")
            
            # Test properties API
            print(f"\n🏠 PROPERTIES API:")
            properties_url = f'{base_url}/api/resident/properties'
            properties_response = requests.get(properties_url, headers=headers, timeout=10)
            print(f"   Status: {properties_response.status_code}")
            
            if properties_response.status_code == 200:
                properties_data = properties_response.json()
                print(f"   Type: {type(properties_data)}")
                print(f"   Is Array: {isinstance(properties_data, list)}")
                print(f"   Length: {len(properties_data) if isinstance(properties_data, list) else 'N/A'}")
            
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_frontend_api()
