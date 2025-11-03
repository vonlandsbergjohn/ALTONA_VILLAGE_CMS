#!/usr/bin/env python3
"""
Update admin user password to the correct one.
"""

import psycopg2
import os
from werkzeug.security import generate_password_hash

DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://postgres:%23Johnvonl1977@localhost:5432/altona_village_db")

def update_admin_password():
    """Set the admin user password to the correct one"""
    
    print("🔧 Updating Admin Password")
    print("=" * 30)
    
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Check current admin user
        cursor.execute("SELECT id, email, role FROM users WHERE email = %s", ('vonlandsbergjohn@gmail.com',))
        admin = cursor.fetchone()
        
        if admin:
            print(f"Found admin: {admin[1]}") # type: ignore
            
            # Set password to the correct one
            correct_password = "dGdFHLCJxx44ykq"
            password_hash = generate_password_hash(correct_password)
            
            cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (password_hash, admin[0])) # type: ignore
            conn.commit()
            
            print(f"✅ Admin password updated to: {correct_password}")
            print(f"✅ Email: {admin[1]}") # type: ignore
        else:
            print("❌ No admin user found")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    update_admin_password()
