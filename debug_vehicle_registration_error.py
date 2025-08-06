#!/usr/bin/env python3
"""
Test vehicle registration directly to see what the actual error is
"""

import requests
import json

def test_vehicle_registration_error():
    print("🚗 TESTING VEHICLE REGISTRATION - FINDING EXACT ERROR")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    # Step 1: Login as the multi-property user
    print("Step 1: Logging in as multi-property user...")
    login_data = {
        "email": "johanvonlandsberg080808@gmail.com",
        "password": "test"
    }
    
    try:
        login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            jwt_token = login_result.get('access_token')
            
            user_headers = {
                "Authorization": f"Bearer {jwt_token}",
                "Content-Type": "application/json"
            }
            print("✅ User login successful")
            print(f"User ID: {login_result['user']['id']}")
            
            # Step 2: Test different vehicle registration scenarios
            print("\nStep 2: Testing vehicle registration scenarios...")
            
            # Test scenario 1: With erf_number field (like frontend sends)
            print("\n🧪 Test 1: With erf_number field")
            test_data_1 = {
                "registration_number": "ERROR1GP",
                "make": "Audi",
                "model": "A4",
                "color": "Black",
                "erf_number": "27681"  # This is what frontend likely sends
            }
            
            response_1 = requests.post(
                f"{base_url}/api/resident/vehicles",
                json=test_data_1,
                headers=user_headers
            )
            
            print(f"Response 1 status: {response_1.status_code}")
            print(f"Response 1 body: {response_1.text}")
            
            # Test scenario 2: Without any ERF specification
            print("\n🧪 Test 2: Without ERF specification")
            test_data_2 = {
                "registration_number": "ERROR2GP",
                "make": "Mercedes",
                "model": "C-Class",
                "color": "Silver"
                # No ERF specified
            }
            
            response_2 = requests.post(
                f"{base_url}/api/resident/vehicles",
                json=test_data_2,
                headers=user_headers
            )
            
            print(f"Response 2 status: {response_2.status_code}")
            print(f"Response 2 body: {response_2.text}")
            
            # Test scenario 3: With target_user_id (checking if this is expected)
            print("\n🧪 Test 3: With target_user_id")
            test_data_3 = {
                "registration_number": "ERROR3GP",
                "make": "Volkswagen",
                "model": "Golf",
                "color": "White",
                "target_user_id": login_result['user']['id']  # User's own ID
            }
            
            response_3 = requests.post(
                f"{base_url}/api/resident/vehicles",
                json=test_data_3,
                headers=user_headers
            )
            
            print(f"Response 3 status: {response_3.status_code}")
            print(f"Response 3 body: {response_3.text}")
            
        else:
            print(f"❌ User login failed: {login_response.text}")
            
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    test_vehicle_registration_error()
