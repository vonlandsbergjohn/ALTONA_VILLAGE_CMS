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
    
    # Login first - USING ADMIN CREDENTIALS FOR COMMUNICATION TESTING
    login_url = f'{base_url}/api/auth/login'
    login_data = {
        'email': 'vonlandsbergjohn@gmail.com',  # Admin user
        'password': 'dGdFHLCJxx44ykq'            # Admin password
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
            
            # Test NEW Communication APIs
            print(f"\n📧 COMMUNICATION STATS API:")
            comm_stats_url = f'{base_url}/api/communication/stats'
            comm_stats_response = requests.get(comm_stats_url, headers=headers, timeout=10)
            print(f"   Status: {comm_stats_response.status_code}")
            
            if comm_stats_response.status_code == 200:
                try:
                    stats_data = comm_stats_response.json()
                    print(f"   Type: {type(stats_data)}")
                    print(f"   Data: {stats_data}")
                except Exception as json_error:
                    print(f"   JSON Parse Error: {json_error}")
                    print(f"   Raw Response: {comm_stats_response.text}")
            else:
                print(f"   Error: {comm_stats_response.status_code} - {comm_stats_response.text}")
            
            # Test Find User by ERF API
            print(f"\n🔍 FIND USER BY ERF API:")
            find_user_url = f'{base_url}/api/communication/find-user-by-erf'
            find_user_data = {'erf_number': '27681'}  # Test with known ERF
            find_user_response = requests.post(find_user_url, json=find_user_data, headers=headers, timeout=10)
            print(f"   Status: {find_user_response.status_code}")
            
            if find_user_response.status_code == 200:
                try:
                    user_data = find_user_response.json()
                    print(f"   Found: {user_data.get('found')}")
                    if user_data.get('found'):
                        user_info = user_data.get('user', {})
                        print(f"   User: {user_info.get('full_name')} ({user_info.get('email')})")
                        print(f"   ERF: {user_info.get('erf_number')} - Type: {user_info.get('type')}")
                except Exception as json_error:
                    print(f"   JSON Parse Error: {json_error}")
            else:
                print(f"   Error Response: {find_user_response.status_code} - {find_user_response.text}")
        
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_frontend_api()
