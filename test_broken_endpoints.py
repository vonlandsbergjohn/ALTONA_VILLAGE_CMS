#!/usr/bin/env python3
"""
Test script to check all API endpoints that are reported as broken
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

# Test admin credentials (you'll need to login first to get a token)
def test_login():
    """Test login to get admin token"""
    login_data = {
        "email": "vonlandsbergjohn@gmail.com",  # Adjust based on your admin user
        "password": "admin123"  # Adjust based on your admin password
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Login Response: {response.status_code}")
        if response.status_code == 200:
            token = response.json().get('access_token')
            print(f"Login successful, got token")
            return token
        else:
            print(f"Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def test_gate_register(token):
    """Test gate register endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/gate-register", headers=headers)
        print(f"\nGate Register Response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Gate register data entries: {data.get('total_entries', 'unknown')}")
            if 'data' in data:
                print(f"First few entries: {data['data'][:2] if data['data'] else 'No entries'}")
        else:
            print(f"Gate register failed: {response.text}")
    except Exception as e:
        print(f"Gate register error: {e}")

def test_admin_users(token):
    """Test admin users endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/admin/users", headers=headers)
        print(f"\nAdmin Users Response: {response.status_code}")
        if response.status_code == 200:
            users = response.json()
            print(f"Total users found: {len(users)}")
            for user in users[:2]:  # Show first 2 users
                print(f"  User: {user.get('email')} - Status: {user.get('status')} - Role: {user.get('role')}")
        else:
            print(f"Admin users failed: {response.text}")
    except Exception as e:
        print(f"Admin users error: {e}")

def test_profile_update(token):
    """Test profile update endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # First get current profile
    try:
        response = requests.get(f"{BASE_URL}/auth/profile", headers=headers)
        print(f"\nProfile Get Response: {response.status_code}")
        if response.status_code != 200:
            print(f"Profile get failed: {response.text}")
            return
        
        profile = response.json()
        print(f"Current profile tenant_or_owner: {profile.get('tenant_or_owner')}")
        
        # Try to update something simple
        update_data = {
            "phone": "0123456789"  # Simple phone update
        }
        
        response = requests.put(f"{BASE_URL}/auth/profile", json=update_data, headers=headers)
        print(f"Profile Update Response: {response.status_code}")
        if response.status_code == 200:
            print("Profile update successful")
        else:
            print(f"Profile update failed: {response.text}")
            
    except Exception as e:
        print(f"Profile update error: {e}")

def test_admin_user_update(token):
    """Test admin user update endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get a user to update (non-admin user)
    try:
        response = requests.get(f"{BASE_URL}/admin/users", headers=headers)
        if response.status_code != 200:
            print("Cannot get users for admin update test")
            return
        
        users = response.json()
        test_user = None
        for user in users:
            if user.get('role') != 'admin':
                test_user = user
                break
        
        if not test_user:
            print("No non-admin user found for update test")
            return
        
        print(f"\nTesting admin update for user: {test_user.get('email')}")
        
        # Try simple update
        update_data = {
            "phone": "0987654321"
        }
        
        response = requests.put(f"{BASE_URL}/admin/update-resident/{test_user['id']}", 
                              json=update_data, headers=headers)
        print(f"Admin User Update Response: {response.status_code}")
        if response.status_code == 200:
            print("Admin user update successful")
        else:
            print(f"Admin user update failed: {response.text}")
            
    except Exception as e:
        print(f"Admin user update error: {e}")

def main():
    print("Testing broken API endpoints...")
    
    # Get auth token
    token = test_login()
    if not token:
        print("Cannot proceed without authentication token")
        return
    
    # Test all reported broken endpoints
    test_gate_register(token)
    test_admin_users(token)
    test_profile_update(token)
    test_admin_user_update(token)
    
    print("\nTesting complete!")

if __name__ == "__main__":
    main()
