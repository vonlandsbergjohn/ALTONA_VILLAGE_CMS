#!/usr/bin/env python3
"""
Set Admin Password using SQLAlchemy models.

This script finds a user by email with the 'admin' role and updates their
password and status. If no such admin user exists, it creates a new one.
This approach is more robust as it uses the application's models.
"""

import os
import sys

# --- Add project root to sys.path to allow for `src` imports ---
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from altona_village_cms.src.main import app
from altona_village_cms.src.models.user import db, User
from werkzeug.security import generate_password_hash

def set_admin_password():
    """Finds or creates an admin user and sets their password."""
    
    admin_email = "vonlandsbergjohn@gmail.com"
    new_password = "dGdFHLCJxx44ykq"
    
    with app.app_context():
        try:
            # Step 1: Check if an admin user with this email already exists.
            admin_user = User.query.filter_by(email=admin_email, role='admin').first()

            if admin_user:
                # Step 2a: If admin exists, update their password and status.
                admin_user.set_password(new_password)
                admin_user.status = 'active'
                print(f"✅ Admin user '{admin_email}' found and updated.")
            else:
                # Step 2b: If no admin exists, create a new one.
                admin_user = User(
                    email=admin_email,
                    role='admin',
                    status='active'
                )
                admin_user.set_password(new_password)
                db.session.add(admin_user)
                print(f"✅ Admin user '{admin_email}' not found. Created a new admin user.")

            db.session.commit()
            print(f"   Role set to: admin")
            print(f"   Status set to: active")
            print(f"   Password set to: {new_password}")

        except Exception as e:
            db.session.rollback()
            print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    print("🔧 Ensuring Admin User Credentials and Status (using SQLAlchemy)...")
    set_admin_password()