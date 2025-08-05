#!/usr/bin/env python3

import requests
import json

def detailed_login_analysis():
    """Detailed analysis of login failures"""
    
    base_url = "http://localhost:5000/api/auth"
    
    # Test with the specific credentials you mentioned
    test_email = "testuser@example.com"  # The user we created earlier
    test_password = "test"
    
    print("=== Detailed Login Analysis ===\n")
    
    # Test 1: Check if user exists and status
    print("1. Testing login with detailed error analysis...")
    
    login_data = {
        "email": test_email,
        "password": test_password
    }
    
    try:
        response = requests.post(f"{base_url}/login", json=login_data)
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            try:
                response_data = response.json()
                print(f"   Response JSON: {json.dumps(response_data, indent=2)}")
            except:
                print(f"   Response (invalid JSON): {response.text}")
        else:
            print(f"   Response Text: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Request error: {e}")
    
    # Test 2: Try with admin credentials to confirm they still work
    print(f"\n2. Testing admin login for comparison...")
    
    admin_login_data = {
        "email": "vonlandsbergjohn@gmail.com",
        "password": "dGdFHLCJxx44ykq"
    }
    
    try:
        response = requests.post(f"{base_url}/login", json=admin_login_data)
        print(f"   Admin login status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Admin login still works")
        else:
            try:
                response_data = response.json()
                print(f"   ❌ Admin login failed: {response_data.get('error', 'Unknown error')}")
            except:
                print(f"   ❌ Admin login failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Admin login error: {e}")
    
    # Test 3: Try different variations
    print(f"\n3. Testing variations...")
    
    variations = [
        {"email": test_email, "password": ""},  # Empty password
        {"email": test_email, "password": "wrong"},  # Wrong password
        {"email": "nonexistent@example.com", "password": test_password},  # Wrong email
        {"email": "", "password": test_password},  # Empty email
    ]
    
    for i, variation in enumerate(variations, 1):
        print(f"   Variation {i}: email='{variation['email']}', password='{variation['password']}'")
        try:
            response = requests.post(f"{base_url}/login", json=variation)
            print(f"     Status: {response.status_code}")
            if response.status_code != 200:
                try:
                    response_data = response.json()
                    print(f"     Error: {response_data.get('error', 'Unknown')}")
                except:
                    print(f"     Error: {response.text}")
        except Exception as e:
            print(f"     Request error: {e}")

if __name__ == "__main__":
    detailed_login_analysis()
