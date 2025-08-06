#!/usr/bin/env python3
"""
Debug the deletion API endpoint to find the 500 error
"""

import requests
import json

def debug_deletion_api():
    print("🐛 DEBUGGING DELETION API ERROR")
    print("=" * 50)
    
    # First, let's get an admin token
    print("1. Testing login to get admin token...")
    login_data = {
        "email": "vonlandsbergjohn@gmail.com",  # Replace with actual admin email
        "password": "password123"  # Replace with actual admin password
    }
    
    try:
        login_response = requests.post('http://localhost:5000/api/auth/login', json=login_data)
        print(f"   Login status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            token = login_response.json().get('access_token')
            print("   ✅ Got admin token")
            
            # Test the deletion endpoint
            print("\n2. Testing deletion endpoint...")
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            deletion_data = {
                "deletion_reason": "Test deletion - debugging API error",
                "confirm_deletion": True
            }
            
            # Use a test user ID (replace with actual user ID from your system)
            user_id = "a65240a7-fe4c-4089-ac87-b1fab754eca7"
            
            delete_response = requests.delete(
                f'http://localhost:5000/api/admin/users/{user_id}/permanent-delete',
                json=deletion_data,
                headers=headers
            )
            
            print(f"   Delete status: {delete_response.status_code}")
            print(f"   Response: {delete_response.text}")
            
            if delete_response.status_code == 500:
                print("   ❌ 500 Error found - checking response details...")
                try:
                    error_details = delete_response.json()
                    print(f"   Error details: {error_details}")
                except:
                    print(f"   Raw response: {delete_response.text}")
            
        else:
            print(f"   ❌ Login failed: {login_response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    debug_deletion_api()
