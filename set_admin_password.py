#!/usr/bin/env python3
"""
Set Admin Password and Consolidate Admin User.

This script finds or creates an admin user, sets their password to a known
value, and ensures they are active. It also disables any duplicate non-admin
accounts with the same email to prevent login conflicts.

Usage (from the project root directory):
source venv/bin/activate
python set_admin_password.py
"""

import os
import sys
import uuid
from werkzeug.security import generate_password_hash

# --- Add project root to sys.path to allow for `src` imports ---
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from altona_village_cms.src.main import create_app
from altona_village_cms.src.models.user import db, User

def ensure_admin_credentials():
    """Finds or creates an admin user and sets their password."""
    admin_email = "vonlandsbergjohn@gmail.com"
    new_password = "dGdFHLCJxx44ykq"
    
    app = create_app()
    
    with app.app_context():
        try:
            # Find all users with this email, regardless of role
            all_users = User.query.filter_by(email=admin_email).all()
            admin_user = next((u for u in all_users if u.role == 'admin'), None)

            if not admin_user:
                # If no admin user exists, create one
                print(f"Admin user '{admin_email}' not found. Creating a new one.")
                admin_user = User(email=admin_email, role='admin')
                db.session.add(admin_user)

            # 1. Set the admin user's password and ensure they are active
            admin_user.set_password(new_password)
            admin_user.status = 'active'
            print(f"✅ Admin user '{admin_user.email}' is being configured.")

            # 2. Disable any other conflicting non-admin users with the same email
            for user in all_users:
                if user.id != admin_user.id:
                    user.status = 'inactive' # Mark as inactive
                    print(f"   - Disabling conflicting non-admin account (ID: {user.id})")

            db.session.commit()
            print("\n✅ Success! Admin credentials have been set.")
            print(f"   - Email:    {admin_email}")
            print(f"   - Password: {new_password}")

        except Exception as e:
            db.session.rollback()
            print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    print("🔧 Ensuring Admin User Credentials and Status...")
    ensure_admin_credentials()