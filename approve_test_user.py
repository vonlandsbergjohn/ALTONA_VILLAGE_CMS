#!/usr/bin/env python3

import requests
import json

def approve_test_user():
    """Approve the test user so they can login"""
    
    base_url = "http://localhost:5000/api"
    
    # Admin credentials
    admin_email = "vonlandsbergjohn@gmail.com"
    admin_password = "dGdFHLCJxx44ykq"
    
    # Test user email
    test_email = "testuser@example.com"
    
    print("=== Approving Test User ===\n")
    
    # Step 1: Login as admin
    print("1. Logging in as admin...")
    admin_login_data = {
        "email": admin_email,
        "password": admin_password
    }
    
    try:
        response = requests.post(f"{base_url}/auth/login", json=admin_login_data)
        if response.status_code == 200:
            admin_token = response.json()['access_token']
            print("   ✅ Admin login successful")
        else:
            print(f"   ❌ Admin login failed: {response.text}")
            return
    except Exception as e:
        print(f"   ❌ Admin login error: {e}")
        return
    
    # Step 2: Get pending registrations
    print("\n2. Getting pending registrations...")
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{base_url}/admin/pending-registrations", headers=headers)
        if response.status_code == 200:
            pending_data = response.json()
            pending_users = pending_data.get('data', [])
            
            print(f"   Found {len(pending_users)} pending users:")
            test_user = None
            
            for user in pending_users:
                print(f"     - {user['email']} (ID: {user['id']}, Status: {user['status']})")
                if user['email'] == test_email:
                    test_user = user
            
            if test_user:
                print(f"\n3. Approving user {test_email}...")
                response = requests.post(f"{base_url}/admin/approve-registration/{test_user['id']}", 
                                       headers=headers)
                if response.status_code == 200:
                    print("   ✅ User approved successfully!")
                    
                    # Step 3: Test login immediately
                    print("\n4. Testing login after approval...")
                    login_data = {
                        "email": test_email,
                        "password": "test"
                    }
                    
                    response = requests.post(f"{base_url}/auth/login", json=login_data)
                    if response.status_code == 200:
                        data = response.json()
                        print("   ✅ Login successful after approval!")
                        print(f"   User Status: {data['user']['status']}")
                        print(f"   User Role: {data['user']['role']}")
                    else:
                        try:
                            error_data = response.json()
                            print(f"   ❌ Login still failed: {error_data.get('error')}")
                        except:
                            print(f"   ❌ Login still failed: {response.text}")
                        
                else:
                    print(f"   ❌ User approval failed: {response.text}")
            else:
                print(f"\n   ℹ️ User {test_email} not found in pending registrations")
                print("   This user might already be approved or doesn't exist")
                
        else:
            print(f"   ❌ Failed to get pending registrations: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    approve_test_user()
