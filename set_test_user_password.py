#!/usr/bin/env python3
"""
Set password for test user.
"""

import psycopg2
import os
from werkzeug.security import generate_password_hash

DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://postgres:%23Johnvonl1977@localhost:5432/altona_village_db")

def set_test_user_password():
    """Set password for the test user"""
    
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Set password for test user
        test_email = "johanvonlandsberg080808@gmai.com"
        password = "dGdFHLCJxx44ykq"
        password_hash = generate_password_hash(password)
        
        cursor.execute("UPDATE users SET password_hash = %s WHERE email = %s", (password_hash, test_email))
        rows_affected = cursor.rowcount
        
        conn.commit()
        
        print(f"✅ Updated password for {rows_affected} user accounts with email {test_email}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    set_test_user_password()
