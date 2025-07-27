#!/usr/bin/env python3
"""
Test the admin residents endpoint to check if intercom_code is included
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_admin_residents_intercom_code():
    """Test that admin residents endpoint returns intercom_code"""
    
    print("🧪 Testing Admin Residents intercom_code...")
    
    # Test data
    login_data = {
        "email": "admin@altonavillage.com",
        "password": "admin123"
    }
    
    try:
        # Login to get token
        print("1. Logging in as admin...")
        login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return False
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get all residents
        print("2. Fetching all residents...")
        residents_response = requests.get(f"{BASE_URL}/admin/residents", headers=headers)
        if residents_response.status_code != 200:
            print(f"❌ Residents fetch failed: {residents_response.status_code}")
            print(f"Response: {residents_response.text}")
            return False
        
        residents_data = residents_response.json()
        print(f"✓ Found {len(residents_data)} residents")
        
        # Check if any residents have intercom_code data
        residents_with_intercom = []
        for i, resident in enumerate(residents_data[:3]):  # Check first 3 residents
            print(f"\n--- Resident {i+1} ---")
            print(f"Name: {resident.get('first_name', 'N/A')} {resident.get('last_name', 'N/A')}")
            print(f"Email: {resident.get('email', 'N/A')}")
            print(f"Intercom Code: '{resident.get('intercom_code', 'NOT_FOUND')}'")
            
            if 'intercom_code' in resident:
                residents_with_intercom.append(resident)
            else:
                print("❌ intercom_code field missing from resident data!")
        
        if residents_with_intercom:
            print(f"\n✅ SUCCESS: {len(residents_with_intercom)} residents have intercom_code field")
            
            # Check if any actually have values
            residents_with_values = [r for r in residents_with_intercom if r.get('intercom_code')]
            if residents_with_values:
                print(f"✅ BONUS: {len(residents_with_values)} residents have intercom_code values")
                for r in residents_with_values:
                    print(f"   - {r.get('first_name')} {r.get('last_name')}: '{r.get('intercom_code')}'")
            else:
                print("ℹ️  No residents currently have intercom_code values set")
            
            return True
        else:
            print("❌ FAILURE: No residents have intercom_code field")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_admin_residents_intercom_code()
    if success:
        print("\n🎉 Admin residents endpoint includes intercom_code!")
    else:
        print("\n💥 Admin residents endpoint missing intercom_code!")
