#!/usr/bin/env python3
"""
Simple test to check user data structure after login
"""
import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_user_data():
    # Test with existing user
    login_data = {
        "email": "hi@hi",  # From the screenshot
        "password": "test123"  # Common test password
    }
    
    try:
        # Login
        print("Testing login...")
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            user_data = data.get('user', {})
            
            print("✅ Login successful!")
            print(f"User ID: {user_data.get('id')}")
            print(f"Email: {user_data.get('email')}")
            print(f"Role: {user_data.get('role')}")
            print(f"Status: {user_data.get('status')}")
            print(f"is_resident: {user_data.get('is_resident')}")
            print(f"is_owner: {user_data.get('is_owner')}")
            print(f"full_name: {user_data.get('full_name')}")
            print(f"Has resident data: {'resident' in user_data}")
            print(f"Has owner data: {'owner' in user_data}")
            
            # Test profile endpoint
            print("\n" + "="*50)
            print("Testing profile endpoint...")
            
            token = data.get('access_token')
            headers = {"Authorization": f"Bearer {token}"}
            
            profile_response = requests.get(f"{BASE_URL}/auth/profile", headers=headers)
            if profile_response.status_code == 200:
                profile_data = profile_response.json()
                print("✅ Profile endpoint successful!")
                print(f"tenant_or_owner: {profile_data.get('tenant_or_owner')}")
                print(f"full_name: {profile_data.get('full_name')}")
                print("Full profile data:")
                print(json.dumps(profile_data, indent=2))
            else:
                print(f"❌ Profile endpoint failed: {profile_response.status_code}")
                print(profile_response.text)
        
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_user_data()
