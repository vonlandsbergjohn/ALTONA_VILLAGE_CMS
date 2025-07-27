#!/usr/bin/env python3
"""
Test script to verify the intercom_code field functionality
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_intercom_code_functionality():
    """Test the intercom_code field in profile management"""
    
    print("🧪 Testing intercom_code functionality...")
    
    # Test data
    login_data = {
        "email": "admin@altonavillage.com",
        "password": "admin123"
    }
    
    try:
        # Login to get token
        print("1. Logging in...")
        login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return False
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get current profile
        print("2. Getting current profile...")
        profile_response = requests.get(f"{BASE_URL}/auth/profile", headers=headers)
        if profile_response.status_code != 200:
            print(f"❌ Profile fetch failed: {profile_response.status_code}")
            return False
        
        current_profile = profile_response.json()
        print(f"✓ Current profile loaded")
        
        # Test updating profile with intercom_code
        print("3. Testing intercom_code update...")
        test_intercom_code = "1234"
        update_data = {
            "intercom_code": test_intercom_code
        }
        
        update_response = requests.put(f"{BASE_URL}/auth/profile", json=update_data, headers=headers)
        if update_response.status_code != 200:
            print(f"❌ Profile update failed: {update_response.status_code}")
            print(f"Response: {update_response.text}")
            return False
        
        print(f"✓ Profile updated with intercom_code: {test_intercom_code}")
        
        # Verify the update
        print("4. Verifying the update...")
        verify_response = requests.get(f"{BASE_URL}/auth/profile", headers=headers)
        if verify_response.status_code != 200:
            print(f"❌ Profile verification failed: {verify_response.status_code}")
            return False
        
        updated_profile = verify_response.json()
        if updated_profile.get("intercom_code") == test_intercom_code:
            print(f"✅ Intercom code successfully updated and verified: {test_intercom_code}")
            return True
        else:
            print(f"❌ Intercom code not properly saved. Expected: {test_intercom_code}, Got: {updated_profile.get('intercom_code')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_intercom_code_functionality()
    if success:
        print("🎉 All tests passed!")
    else:
        print("💥 Tests failed!")
