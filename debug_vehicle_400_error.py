#!/usr/bin/env python3
"""
Debug script to test vehicle registration API and identify the 400 Bad Request issue
"""

import requests
import json

def test_vehicle_registration_debug():
    """Debug the vehicle registration 400 error"""
    
    print("🔍 VEHICLE REGISTRATION DEBUG")
    print("=" * 50)
    
    # Test different ports to find the working frontend
    frontend_ports = [5173, 5174]
    backend_port = 5000
    
    working_frontend = None
    
    # Step 1: Find which frontend port is working
    print("\n1️⃣ Testing Frontend Ports...")
    for port in frontend_ports:
        try:
            response = requests.get(f"http://localhost:{port}/api/public/erf-lookup/27682", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ Frontend working on port {port}")
                working_frontend = port
                break
            else:
                print(f"   ❌ Port {port} returned {response.status_code}")
        except Exception as e:
            print(f"   ❌ Port {port} not accessible: {str(e)[:50]}...")
    
    if not working_frontend:
        print("   ❌ No working frontend found!")
        return
    
    # Step 2: Test backend directly
    print(f"\n2️⃣ Testing Backend Direct (Port {backend_port})...")
    try:
        # Login to backend directly
        login_response = requests.post(f"http://localhost:{backend_port}/api/auth/login",
                                     json={'email': 'johanvonlandsberg080808@gmail.com', 'password': 'test'},
                                     timeout=10)
        print(f"   Backend Login: {login_response.status_code}")
        
        if login_response.status_code == 200:
            token = login_response.json().get('access_token')
            
            # Test vehicle registration directly to backend
            headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
            vehicle_data = {
                'make': 'Debug',
                'model': 'Test',
                'year': 2024,
                'color': 'Blue',
                'registration_number': 'DEBUG123',
                'erf_number': '27682'
            }
            
            vehicle_response = requests.post(f"http://localhost:{backend_port}/api/resident/vehicles",
                                           headers=headers, json=vehicle_data, timeout=10)
            print(f"   Backend Vehicle Registration: {vehicle_response.status_code}")
            if vehicle_response.status_code != 201:
                print(f"   Backend Error: {vehicle_response.text}")
        
    except Exception as e:
        print(f"   ❌ Backend error: {e}")
    
    # Step 3: Test through frontend proxy
    print(f"\n3️⃣ Testing Through Frontend Proxy (Port {working_frontend})...")
    try:
        # Login through frontend proxy
        login_response = requests.post(f"http://localhost:{working_frontend}/api/auth/login",
                                     json={'email': 'johanvonlandsberg080808@gmail.com', 'password': 'test'},
                                     timeout=10)
        print(f"   Proxy Login: {login_response.status_code}")
        
        if login_response.status_code == 200:
            token = login_response.json().get('access_token')
            
            # Test vehicle registration through proxy
            headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
            vehicle_data = {
                'make': 'Proxy',
                'model': 'Test',
                'year': 2024,
                'color': 'Red',
                'registration_number': 'PROXY456',
                'erf_number': '27682'
            }
            
            vehicle_response = requests.post(f"http://localhost:{working_frontend}/api/resident/vehicles",
                                           headers=headers, json=vehicle_data, timeout=10)
            print(f"   Proxy Vehicle Registration: {vehicle_response.status_code}")
            if vehicle_response.status_code != 201:
                print(f"   Proxy Error: {vehicle_response.text}")
                print(f"   Response Headers: {dict(vehicle_response.headers)}")
        
    except Exception as e:
        print(f"   ❌ Proxy error: {e}")
    
    # Step 4: Test with different data formats
    print(f"\n4️⃣ Testing Different Data Formats...")
    try:
        # Login through frontend proxy
        login_response = requests.post(f"http://localhost:{working_frontend}/api/auth/login",
                                     json={'email': 'johanvonlandsberg080808@gmail.com', 'password': 'test'},
                                     timeout=10)
        
        if login_response.status_code == 200:
            token = login_response.json().get('access_token')
            headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
            
            # Test 1: Minimal required fields only
            minimal_data = {
                'registration_number': 'MIN123',
                'make': 'Test',
                'model': 'Car',
                'color': 'Blue'
            }
            
            response1 = requests.post(f"http://localhost:{working_frontend}/api/resident/vehicles",
                                    headers=headers, json=minimal_data, timeout=10)
            print(f"   Minimal Data: {response1.status_code}")
            if response1.status_code != 201:
                print(f"     Error: {response1.text}")
            
            # Test 2: With ERF for multi-property user
            with_erf_data = {
                'registration_number': 'ERF123',
                'make': 'Test',
                'model': 'Car',
                'color': 'Blue',
                'erf_number': '27682'
            }
            
            response2 = requests.post(f"http://localhost:{working_frontend}/api/resident/vehicles",
                                    headers=headers, json=with_erf_data, timeout=10)
            print(f"   With ERF Data: {response2.status_code}")
            if response2.status_code != 201:
                print(f"     Error: {response2.text}")
                
            # Test 3: With all fields
            complete_data = {
                'registration_number': 'FULL123',
                'make': 'Test',
                'model': 'Car',
                'year': 2024,
                'color': 'Blue',
                'vehicle_type': 'car',
                'erf_number': '27682'
            }
            
            response3 = requests.post(f"http://localhost:{working_frontend}/api/resident/vehicles",
                                    headers=headers, json=complete_data, timeout=10)
            print(f"   Complete Data: {response3.status_code}")
            if response3.status_code != 201:
                print(f"     Error: {response3.text}")
        
    except Exception as e:
        print(f"   ❌ Data format test error: {e}")
    
    print(f"\n" + "=" * 50)
    print("🔍 DEBUG COMPLETE")
    print("\nNext steps:")
    print("1. Check which port your browser is actually using")
    print("2. Make sure you're accessing the correct frontend URL")
    print("3. Clear browser cache and try again")
    print("4. Check browser developer tools Network tab for exact error details")

if __name__ == "__main__":
    test_vehicle_registration_debug()
