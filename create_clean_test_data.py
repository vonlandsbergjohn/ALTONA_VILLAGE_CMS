#!/usr/bin/env python3
"""
Create clean test data for transition system testing
"""
import requests
import json

BASE_URL = "http://localhost:5000/api"

def create_admin_user():
    """Create an admin user"""
    admin_data = {
        "first_name": "Admin",
        "last_name": "User", 
        "email": "admin@altonavillage.com",
        "password": "admin123",
        "phone_number": "555-0001",
        "emergency_contact_name": "Emergency Contact",
        "emergency_contact_number": "555-0002",
        "id_number": "8001010001080",
        "address": "Admin Office",
        "is_owner": False,
        "is_resident": False
    }
    
    print("Creating admin user...")
    response = requests.post(f"{BASE_URL}/auth/register", json=admin_data)
    if response.status_code == 201:
        print("✅ Admin user created")
        
        # Login and get token
        login_response = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "admin@altonavillage.com",
            "password": "admin123"
        })
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            user_id = login_response.json()["user"]["id"]
            
            # Update user to admin role directly in database
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), 'altona_village_cms', 'src'))
            
            from models.user import User
            from database.connection import db
            from app import create_app
            
            app = create_app()
            with app.app_context():
                user = User.query.get(user_id)
                if user:
                    user.role = 'admin'
                    user.status = 'approved'
                    db.session.commit()
                    print("✅ Admin user role updated")
            
            return token
    else:
        print(f"❌ Failed to create admin user: {response.text}")
        return None

def create_current_user():
    """Create a current user who will request transition"""
    user_data = {
        "first_name": "John",
        "last_name": "Smith",
        "email": "john.smith@example.com", 
        "password": "password123",
        "phone_number": "555-1001",
        "emergency_contact_name": "Jane Smith",
        "emergency_contact_number": "555-1002", 
        "id_number": "8001015001080",
        "address": "ERF 27727, Altona Village",
        "is_owner": True,
        "is_resident": True
    }
    
    print("Creating current user (John Smith)...")
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    if response.status_code == 201:
        print("✅ Current user created")
        
        # Approve the user
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'altona_village_cms', 'src'))
        
        from models.user import User
        from database.connection import db
        from app import create_app
        
        app = create_app()
        with app.app_context():
            user = User.query.filter_by(email="john.smith@example.com").first()
            if user:
                user.status = 'approved'
                db.session.commit()
                print("✅ Current user approved")
        
        return True
    else:
        print(f"❌ Failed to create current user: {response.text}")
        return False

def main():
    print("🧹 CREATING CLEAN TEST DATA")
    print("=" * 50)
    
    # Create admin user
    admin_token = create_admin_user()
    if not admin_token:
        print("❌ Failed to create admin user")
        return
    
    # Create current user
    if not create_current_user():
        print("❌ Failed to create current user")
        return
    
    print("\n✅ Clean test data created successfully!")
    print("\nTest accounts created:")
    print("Admin: admin@altonavillage.com / admin123")
    print("Current User: john.smith@example.com / password123")
    print("\nERF 27727 is now ready for transition testing")

if __name__ == "__main__":
    main()
