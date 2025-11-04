#!/usr/bin/env python3
"""
Set Admin Password for a specific user and ensure they are an active admin.
"""

import os
import uuid
import psycopg2
from werkzeug.security import generate_password_hash

DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://postgres:%23Johnvonl1977@localhost:5432/altona_village_db")

def set_admin_password():
    """Set a user's password and ensure they are an active admin."""
    
    admin_email = "vonlandsbergjohn@gmail.com"
    new_password = "dGdFHLCJxx44ykq"
    
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        password_hash = generate_password_hash(new_password)
        
        # Create or update the admin user in one step.
        # If the email exists, it updates the password, role, and status.
        # If it doesn't exist, it creates the user with these details.
        cursor.execute("""
            INSERT INTO users (id, email, password_hash, role, status)
            VALUES (%s, %s, %s, 'admin', 'active')
            ON CONFLICT (email) DO UPDATE SET
                password_hash = EXCLUDED.password_hash,
                role = EXCLUDED.role,
                status = EXCLUDED.status;
        """, (str(uuid.uuid4()), admin_email, password_hash))
        conn.commit()
        
        print(f"✅ User '{admin_email}' has been updated:")
        print(f"   Role: admin")
        print(f"   Status: active")
        print(f"   Password set to: {new_password}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🔧 Ensuring Admin User Credentials and Status...")
    set_admin_password()
