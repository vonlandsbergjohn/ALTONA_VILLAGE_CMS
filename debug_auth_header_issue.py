#!/usr/bin/env python3
"""
Debug script to test authentication flow and fix missing authorization header issue
"""

import requests
import json

def debug_auth_flow():
    """Debug the authentication flow step by step"""
    
    print("🔐 AUTHENTICATION FLOW DEBUG")
    print("=" * 50)
    
    frontend_url = "http://localhost:5173"
    
    # Step 1: Test login and get token details
    print("\n1️⃣ Testing Login Flow...")
    try:
        login_response = requests.post(f"{frontend_url}/api/auth/login",
                                     json={'email': 'johanvonlandsberg080808@gmail.com', 'password': 'test'},
                                     timeout=10)
        print(f"   Login Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            token = login_data.get('access_token')
            user_info = login_data.get('user', {})
            
            print(f"   ✅ Login successful")
            print(f"   📧 User: {user_info.get('email', 'Unknown')}")
            print(f"   🎫 Token received: {len(token)} characters" if token else "   ❌ No token received")
            print(f"   🔑 Token preview: {token[:20]}..." if token and len(token) > 20 else f"   🔑 Token: {token}")
            
            # Step 2: Test token validation
            print(f"\n2️⃣ Testing Token Validation...")
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            profile_response = requests.get(f"{frontend_url}/api/auth/profile", headers=headers, timeout=10)
            print(f"   Profile Request Status: {profile_response.status_code}")
            
            if profile_response.status_code == 200:
                profile_data = profile_response.json()
                print(f"   ✅ Token is valid")
                print(f"   👤 Profile loaded: {profile_data.get('email', 'Unknown')}")
                
                # Check user's properties for ERF selection
                erfs = profile_data.get('erfs', [])
                print(f"   🏠 User properties: {len(erfs)} ERFs")
                for erf in erfs:
                    print(f"      - ERF {erf.get('erf_number', 'Unknown')}")
                
                return token, profile_data
            else:
                print(f"   ❌ Token validation failed: {profile_response.text}")
                return None, None
        else:
            print(f"   ❌ Login failed: {login_response.text}")
            return None, None
            
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return None, None

def test_vehicle_registration_with_auth(token, user_profile):
    """Test vehicle registration with proper authentication"""
    
    print(f"\n3️⃣ Testing Vehicle Registration with Authentication...")
    
    frontend_url = "http://localhost:5173"
    
    if not token:
        print("   ❌ No token available for testing")
        return
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Test different vehicle registration scenarios
    test_scenarios = [
        {
            "name": "Basic Registration",
            "data": {
                'registration_number': 'AUTH001',
                'make': 'Toyota',
                'model': 'Corolla',
                'color': 'Blue'
            }
        },
        {
            "name": "With ERF Selection",
            "data": {
                'registration_number': 'AUTH002',
                'make': 'Honda',
                'model': 'Civic',
                'color': 'Red',
                'erf_number': '27682'
            }
        },
        {
            "name": "Complete Registration",
            "data": {
                'registration_number': 'AUTH003',
                'make': 'Ford',
                'model': 'Focus',
                'year': 2024,
                'color': 'White',
                'vehicle_type': 'car',
                'erf_number': '27682'
            }
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n   Testing: {scenario['name']}")
        
        try:
            response = requests.post(f"{frontend_url}/api/resident/vehicles",
                                   headers=headers, 
                                   json=scenario['data'], 
                                   timeout=10)
            
            print(f"      Status: {response.status_code}")
            
            if response.status_code == 201:
                result = response.json()
                print(f"      ✅ Success: Vehicle {result.get('registration_number')} registered")
                print(f"      🆔 Vehicle ID: {result.get('id')}")
            else:
                print(f"      ❌ Failed: {response.text}")
                
        except Exception as e:
            print(f"      ❌ Error: {e}")

def test_auth_header_formats():
    """Test different authorization header formats"""
    
    print(f"\n4️⃣ Testing Authorization Header Formats...")
    
    frontend_url = "http://localhost:5173"
    
    # Get a token first
    login_response = requests.post(f"{frontend_url}/api/auth/login",
                                 json={'email': 'johanvonlandsberg080808@gmail.com', 'password': 'test'},
                                 timeout=10)
    
    if login_response.status_code != 200:
        print("   ❌ Cannot get token for header testing")
        return
    
    token = login_response.json().get('access_token')
    
    # Test different header formats
    header_formats = [
        {'Authorization': f'Bearer {token}'},
        {'authorization': f'Bearer {token}'},  # lowercase
        {'Authorization': f'bearer {token}'},  # lowercase bearer
        {'Authorization': token},              # without Bearer prefix
        {}                                     # no header (should fail)
    ]
    
    for i, headers in enumerate(header_formats):
        headers['Content-Type'] = 'application/json'
        
        try:
            response = requests.get(f"{frontend_url}/api/auth/profile", headers=headers, timeout=5)
            status = "✅ Success" if response.status_code == 200 else f"❌ Failed ({response.status_code})"
            header_desc = list(headers.keys())[0] if headers else "No auth header"
            print(f"   Format {i+1}: {header_desc} - {status}")
            
        except Exception as e:
            print(f"   Format {i+1}: Error - {e}")

def main():
    """Main debug function"""
    
    print("🚗 VEHICLE REGISTRATION AUTH DEBUG")
    print("=" * 60)
    print("This script will help identify and fix the 'Missing Authorization Header' error")
    print("")
    
    # Step 1: Debug authentication flow
    token, user_profile = debug_auth_flow()
    
    # Step 2: Test vehicle registration with proper auth
    if token:
        test_vehicle_registration_with_auth(token, user_profile)
    
    # Step 3: Test different header formats
    test_auth_header_formats()
    
    print(f"\n" + "=" * 60)
    print("🎯 TROUBLESHOOTING STEPS:")
    print("1. Make sure you're logged in with fresh credentials")
    print("2. Check that your browser isn't blocking cookies/localStorage")
    print("3. Try logging out and logging back in")
    print("4. Clear browser cache and try again")
    print("5. Check browser Developer Tools → Application → Local Storage")
    print("6. Look for 'token' or 'access_token' in localStorage")
    print("")
    print("If the API tests above work but your browser doesn't:")
    print("- The issue is in the frontend JavaScript token handling")
    print("- Check the browser console for JavaScript errors")
    print("- Verify the frontend is correctly storing and sending tokens")

if __name__ == "__main__":
    main()
