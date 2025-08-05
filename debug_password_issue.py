#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'altona_village_cms', 'src'))

# Import Flask app and initialize database
from main import app
from models.user import User, db

def test_password_issue():
    """Test password login behavior for a user with password 'test'"""
    
    # Initialize the app context and database
    with app.app_context():
        db.init_app(app)
        # Look for a user that might have been registered with 'test' password
        print("=== Testing Password Login Issue ===\n")
        
        # Check all users and their password hashes
        users = User.query.all()
        print(f"Total users in database: {len(users)}")
        
        for user in users:
            print(f"\nUser: {user.email}")
            print(f"  Status: {user.status}")
            print(f"  Role: {user.role}")
            print(f"  Password hash: {user.password_hash}")
            
            # Test password 'test' with this user
            test_result = user.check_password('test')
            print(f"  Password 'test' check result: {test_result}")
            
            # Test the actual stored hash verification
            from werkzeug.security import check_password_hash
            raw_check = check_password_hash(user.password_hash, 'test')
            print(f"  Raw hash check for 'test': {raw_check}")
            
            # If this user should have password 'test', let's verify
            if test_result:
                print(f"  ✅ User {user.email} can login with 'test'")
                
                # Test multiple times to see if it changes
                for i in range(3):
                    multiple_test = user.check_password('test')
                    print(f"    Test #{i+1}: {multiple_test}")
            else:
                print(f"  ❌ User {user.email} cannot login with 'test'")

if __name__ == "__main__":
    test_password_issue()
