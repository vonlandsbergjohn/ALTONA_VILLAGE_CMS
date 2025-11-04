#!/usr/bin/env python3
"""
Set Admin Password for a specific user and ensure they are an active admin.
This script handles cases where the email column is not unique.
"""

import os
import uuid
import psycopg2
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone

DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://postgres:%23Johnvonl1977@localhost:5432/altona_village_db")

def set_admin_password():
    """
    Finds a user by email with the 'admin' role and updates their password and status.
    If no admin user with that email exists, it creates a new one.
    """
    
    admin_email = "vonlandsbergjohn@gmail.com"
    new_password = "dGdFHLCJxx44ykq"
    
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        password_hash = generate_password_hash(new_password)
        
        # Step 1: Check if an admin user with this email already exists.
        cursor.execute("""
            SELECT id FROM users WHERE email = %s AND role = 'admin'
        """, (admin_email,))
        
        admin_user = cursor.fetchone()

        if admin_user:
            # Step 2a: If admin exists, update their password and status.
            admin_id = admin_user[0]
            cursor.execute("""
                UPDATE users SET password_hash = %s, status = 'active'
                WHERE id = %s;
            """, (password_hash, admin_id))
            print(f"✅ Admin user '{admin_email}' found and updated.")
        else:
            # Step 2b: If no admin exists, create a new user with admin role.
            cursor.execute("""
                INSERT INTO users (id, email, password_hash, role, status, created_at, updated_at)
                VALUES (%s, %s, %s, 'admin', 'active', %s, %s);
            """, (str(uuid.uuid4()), admin_email, password_hash, datetime.now(timezone.utc), datetime.now(timezone.utc)))
            print(f"✅ Admin user '{admin_email}' not found. Created a new admin user.")

        conn.commit()
        
        print(f"   Role set to: admin")
        print(f"   Status set to: active")
        print(f"   Password set to: {new_password}")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🔧 Ensuring Admin User Credentials and Status...")
    set_admin_password()