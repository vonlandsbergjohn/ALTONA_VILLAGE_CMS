#!/usr/bin/env python3
"""
Set Admin Password for Testing

This script finds the admin user by email and resets their password to a known value.
Run this from your activated virtual environment whenever you need to reset the admin password.
It also disables any duplicate non-admin accounts with the same email to prevent login conflicts.

Usage:
python set_admin_password.py
"""

import sys
import os
import uuid
from werkzeug.security import generate_password_hash
from flask import Flask

# --- Setup paths to import the app's models ---
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'altona_village_cms', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from models.user import User, db

# --- Create a minimal Flask app to get a database context ---
app = Flask(__name__)

# Use the same database URI as your main application
DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://postgres:%23Johnvonl1977@localhost:5432/altona_village_db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def reset_password():
    """Finds the admin user and sets the password to 'admin123'."""
    with app.app_context():
        admin_email = 'vonlandsbergjohn@gmail.com'
        new_password = 'admin123'

        # Find all users with this email
        all_users = User.query.filter_by(email=admin_email).all()
        admin_user = next((u for u in all_users if u.role == 'admin'), None)

        if not admin_user:
            print(f"❌ Error: Admin user '{admin_email}' not found.")
            return

        # 1. Reset the admin user's password and ensure they are active
        admin_user.set_password(new_password)
        admin_user.status = 'active'
        print(f"✅ Success! Password for admin '{admin_user.email}' has been reset to: {new_password}")

        # 2. Disable any other non-admin users with the same email
        disabled_count = 0
        for user in all_users:
            if user.id != admin_user.id:
                # Set a long, random, unusable password
                user.password_hash = generate_password_hash(str(uuid.uuid4()))
                user.status = 'inactive' # Also mark as inactive
                disabled_count += 1
                print(f"   - Disabled conflicting non-admin account (ID: {user.id})")

        db.session.commit()

if __name__ == "__main__":
    reset_password()