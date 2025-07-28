#!/usr/bin/env python3
"""
Test the fixed intercom_code functionality
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_intercom_code_fix():
    """Test that intercom_code is properly saved and retrieved"""
    
    print("🧪 Testing FIXED intercom_code functionality...")
    
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
            print(f"Response: {login_response.text}")
            return False
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get current profile to see existing intercom_code
        print("2. Getting current profile...")
        profile_response = requests.get(f"{BASE_URL}/auth/profile", headers=headers)
        if profile_response.status_code != 200:
            print(f"❌ Profile fetch failed: {profile_response.status_code}")
            return False
        
        current_profile = profile_response.json()
        print(f"✓ Current profile intercom_code: '{current_profile.get('intercom_code', 'NOT_FOUND')}'")
        
        # Test updating profile with new intercom_code
        print("3. Testing intercom_code update...")
        test_intercom_code = "9999"
        update_data = {
            "intercom_code": test_intercom_code
        }
        
        print(f"   Sending update data: {update_data}")
        update_response = requests.put(f"{BASE_URL}/auth/profile", json=update_data, headers=headers)
        if update_response.status_code != 200:
            print(f"❌ Profile update failed: {update_response.status_code}")
            print(f"Response: {update_response.text}")
            return False
        
        print(f"✓ Profile update response: {update_response.json()}")
        
        # Verify the update by fetching profile again
        print("4. Verifying the update...")
        verify_response = requests.get(f"{BASE_URL}/auth/profile", headers=headers)
        if verify_response.status_code != 200:
            print(f"❌ Profile verification failed: {verify_response.status_code}")
            return False
        
        updated_profile = verify_response.json()
        returned_intercom_code = updated_profile.get('intercom_code')
        
        print(f"   Expected: '{test_intercom_code}'")
        print(f"   Returned: '{returned_intercom_code}'")
        
        if returned_intercom_code == test_intercom_code:
            print(f"✅ SUCCESS: Intercom code properly saved and retrieved!")
            return True
        else:
            print(f"❌ FAILURE: Intercom code mismatch")
            print(f"   Full profile response: {updated_profile}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_intercom_code_fix()
    if success:
        print("\n🎉 Intercom code is now working correctly!")
    else:
        print("\n💥 Intercom code still has issues!")
