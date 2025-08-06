#!/usr/bin/env python3
"""
Debug Multi-ERF User Vehicles API Response
"""

import requests
import json

def debug_vehicles_api():
    base_url = 'http://localhost:5000'
    
    print("🔍 DEBUGGING VEHICLES API RESPONSE")
    print("=" * 40)
    
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
            
            # Test vehicles API with raw response
            headers = {'Authorization': f'Bearer {token}'}
            vehicles_url = f'{base_url}/api/residents/vehicles'
            
            vehicles_response = requests.get(vehicles_url, headers=headers, timeout=10)
            print(f"\n🚗 Vehicles API Response:")
            print(f"   Status Code: {vehicles_response.status_code}")
            print(f"   Content-Type: {vehicles_response.headers.get('Content-Type', 'Unknown')}")
            print(f"   Raw Response: '{vehicles_response.text}'")
            print(f"   Response Length: {len(vehicles_response.text)} characters")
            
            if vehicles_response.text.strip():
                try:
                    vehicles_data = vehicles_response.json()
                    print(f"   Parsed JSON: {vehicles_data}")
                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON Parse Error: {e}")
            else:
                print(f"   ⚠️ Empty response body")
                
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_vehicles_api()
