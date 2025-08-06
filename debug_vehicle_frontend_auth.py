#!/usr/bin/env python3
"""
Debug script to test vehicle registration authentication through frontend proxy
This tests the exact same flow the frontend uses
"""

import requests
import json

def test_frontend_auth_flow():
    """Test the complete authentication and vehicle registration flow through frontend proxy"""
    
    print("🔐 Testing Vehicle Registration Authentication Flow")
    print("=" * 60)
    
    base_url = "http://localhost:5174"
    
    # Step 1: Login to get fresh token
    print("\n1️⃣ Testing Login...")
    login_url = f"{base_url}/api/auth/login"
    login_data = {
        'email': 'johanvonlandsberg080808@gmail.com',
        'password': 'test'
    }
    
    try:
        login_response = requests.post(login_url, json=login_data, timeout=10)
        print(f"   Login Status: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"   ❌ Login failed: {login_response.text}")
            return False
            
        login_result = login_response.json()
        token = login_result.get('access_token')
        print(f"   ✅ Login successful, token received")
        
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return False
    
    # Step 2: Test profile access
    print("\n2️⃣ Testing Profile Access...")
    profile_url = f"{base_url}/api/auth/profile"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    try:
        profile_response = requests.get(profile_url, headers=headers, timeout=10)
        print(f"   Profile Status: {profile_response.status_code}")
        
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            print(f"   ✅ Profile loaded: {profile_data.get('email', 'Unknown')}")
            user_erfs = profile_data.get('erfs', [])
            print(f"   📍 User ERFs: {len(user_erfs)} properties")
            for erf in user_erfs:
                print(f"      - ERF {erf.get('erf_number', 'Unknown')}")
        else:
            print(f"   ⚠️ Profile access issue: {profile_response.text}")
            
    except Exception as e:
        print(f"   ❌ Profile error: {e}")
    
    # Step 3: Test existing vehicles load
    print("\n3️⃣ Testing Load Existing Vehicles...")
    vehicles_url = f"{base_url}/api/resident/vehicles"
    
    try:
        vehicles_response = requests.get(vehicles_url, headers=headers, timeout=10)
        print(f"   Load Vehicles Status: {vehicles_response.status_code}")
        
        if vehicles_response.status_code == 200:
            vehicles_data = vehicles_response.json()
            print(f"   ✅ Vehicles loaded: {len(vehicles_data)} vehicles")
            for vehicle in vehicles_data:
                print(f"      - {vehicle.get('registration_number', 'Unknown')} ({vehicle.get('make', '')} {vehicle.get('model', '')})")
        else:
            print(f"   ❌ Load vehicles failed: {vehicles_response.text}")
            print("   🔍 This could be why you see 'Failed to load vehicles' error")
            
    except Exception as e:
        print(f"   ❌ Load vehicles error: {e}")
    
    # Step 4: Test vehicle registration
    print("\n4️⃣ Testing Vehicle Registration...")
    vehicle_data = {
        'make': 'Test',
        'model': 'Frontend',
        'year': 2024,
        'color': 'Blue',
        'registration_number': 'TEST123',
        'erf_number': '27682'  # Use specific ERF
    }
    
    try:
        register_response = requests.post(vehicles_url, headers=headers, json=vehicle_data, timeout=10)
        print(f"   Vehicle Registration Status: {register_response.status_code}")
        
        if register_response.status_code == 201:
            result = register_response.json()
            print(f"   ✅ Vehicle registered successfully")
            print(f"      ID: {result.get('id', 'Unknown')}")
            print(f"      Registration: {result.get('registration_number', 'Unknown')}")
            print(f"      Owner ID: {result.get('owner_id', 'Unknown')}")
        else:
            print(f"   ❌ Vehicle registration failed: {register_response.text}")
            
    except Exception as e:
        print(f"   ❌ Vehicle registration error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Frontend authentication flow test complete")
    print("\nIf any step failed above, that's the source of your 'Failed to save vehicle' error.")
    print("The most common issues are:")
    print("- Expired JWT tokens (logout/login fixes this)")
    print("- Backend server not responding (check if backend is running)")
    print("- Proxy configuration issues (check Vite proxy settings)")

if __name__ == "__main__":
    test_frontend_auth_flow()
