#!/usr/bin/env python3
"""
Test script to verify resident status change functionality.
This script will test the profile update endpoint with status changes.
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:5000/api"
TEST_EMAIL = "vonlandsbergjohn@gmail.com"  # Use existing admin account
TEST_PASSWORD = "admin123"  # Try common test password

def login():
    """Login and get JWT token"""
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Login successful. Token: {token[:50]}...")
        return token
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None

def get_profile(token):
    """Get current profile"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/auth/profile", headers=headers)
    
    if response.status_code == 200:
        profile = response.json()
        print(f"✅ Profile retrieved:")
        print(f"   Email: {profile.get('email')}")
        print(f"   Current Status: {profile.get('tenant_or_owner')}")
        print(f"   Is Resident: {profile.get('is_resident', 'N/A')}")
        print(f"   Is Owner: {profile.get('is_owner', 'N/A')}")
        return profile
    else:
        print(f"❌ Get profile failed: {response.status_code} - {response.text}")
        return None

def test_status_change(token, new_status):
    """Test changing user status"""
    print(f"\n🔄 Testing status change to: {new_status}")
    
    headers = {"Authorization": f"Bearer {token}"}
    update_data = {
        "tenant_or_owner": new_status
    }
    
    response = requests.put(f"{BASE_URL}/auth/profile", json=update_data, headers=headers)
    
    if response.status_code == 200:
        print(f"✅ Status change successful")
        return True
    else:
        print(f"❌ Status change failed: {response.status_code} - {response.text}")
        return False

def main():
    print("🧪 Testing Resident Status Change Functionality")
    print("=" * 50)
    
    # Step 1: Login
    token = login()
    if not token:
        return
    
    # Step 2: Get initial profile
    print("\n📋 Initial Profile:")
    initial_profile = get_profile(token)
    if not initial_profile:
        return
    
    # Step 3: Test status changes
    statuses_to_test = ["owner", "tenant"]
    
    for status in statuses_to_test:
        if test_status_change(token, status):
            print(f"\n📋 Profile after changing to {status}:")
            get_profile(token)
        
        print("-" * 30)
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    main()
