"""
Script to check and create admin user with correct credentials
Run this to fix admin login issues
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000/api"

# The correct admin credentials from your system
ADMIN_EMAIL = "vonlandsbergjohn@gmail.com"
ADMIN_PASSWORD = "dGdFHLCJxx44ykq"

def check_server():
    """Check if server is running"""
    try:
        response = requests.get("http://localhost:5000/api/public/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def test_admin_login():
    """Test admin login with current credentials"""
    print("🔑 Testing admin login...")
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if response.status_code == 200:
            print("✅ Admin login successful!")
            data = response.json()
            user = data.get('user', {})
            print(f"   User ID: {user.get('id')}")
            print(f"   Email: {user.get('email')}")
            print(f"   Role: {user.get('role')}")
            print(f"   Status: {user.get('status')}")
            return True, data.get('access_token')
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error during login: {e}")
        return False, None

def create_admin_user():
    """Create admin user if it doesn't exist"""
    print("👤 Creating admin user...")
    
    admin_data = {
        "first_name": "John",
        "last_name": "von Landsberg",
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
        "phone_number": "555-0001",
        "emergency_contact_name": "Emergency Contact",
        "emergency_contact_number": "555-0002",
        "id_number": "8001010001080",
        "erf_number": "ADMIN",
        "street_number": "Admin",
        "street_name": "Office",
        "is_owner": False,
        "is_resident": False
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=admin_data)
        
        if response.status_code == 201:
            print("✅ Admin user created successfully")
            return True
        elif response.status_code == 400 and "already exists" in response.text.lower():
            print("ℹ️  Admin user already exists")
            return True
        else:
            print(f"❌ Failed to create admin user: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False

def update_user_to_admin(token):
    """Update user role to admin directly in database"""
    print("🔧 Attempting to update user role to admin...")
    
    # This would typically require direct database access
    # For now, let's try to see if there's an API endpoint
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to get user info first
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            print(f"   Current user role: {user_data.get('role')}")
            
            if user_data.get('role') != 'admin':
                print("   ⚠️  User exists but is not admin")
                print("   💡 You may need to manually update the database")
                print("   SQL: UPDATE users SET role = 'admin' WHERE email = 'vonlandsbergjohn@gmail.com';")
                return False
            else:
                print("   ✅ User already has admin role")
                return True
        else:
            print(f"   ❌ Could not get user info: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking user role: {e}")
        return False

def main():
    print("🏘️  Altona Village CMS - Admin Login Fix")
    print("=" * 50)
    
    # Check server
    if not check_server():
        print("❌ Backend server is not running!")
        print("💡 Start the server first:")
        print("   1. Use VS Code task: 'Start Backend'")
        print("   2. Or run: python altona_village_cms/src/main.py")
        return
    
    print("✅ Backend server is running")
    print("")
    
    # Test current login
    success, token = test_admin_login()
    
    if success:
        print("\n🎉 Admin login is working!")
        print(f"📧 Email: {ADMIN_EMAIL}")
        print(f"🔑 Password: {ADMIN_PASSWORD}")
        return
    
    print("\n🔧 Admin login failed. Attempting to fix...")
    
    # Try to create admin user
    if create_admin_user():
        print("\n🔄 Retesting admin login...")
        success, token = test_admin_login()
        
        if success:
            print("\n🎉 Admin login now working!")
        else:
            print("\n⚠️  User created but login still failing")
            print("💡 The user might not have admin role")
            
            if token:
                update_user_to_admin(token)
    
    print("\n" + "=" * 50)
    print("📋 Summary:")
    print(f"   Email: {ADMIN_EMAIL}")
    print(f"   Password: {ADMIN_PASSWORD}")
    print("")
    print("💡 If login still fails, try:")
    print("   1. Check database for user record")
    print("   2. Verify user.role = 'admin'") 
    print("   3. Verify user.status = 'active'")
    print("   4. Check password hash matches")

if __name__ == "__main__":
    main()
