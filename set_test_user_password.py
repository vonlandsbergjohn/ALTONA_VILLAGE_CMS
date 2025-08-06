#!/usr/bin/env python3
"""
Set password for test user.
"""

import sqlite3
from werkzeug.security import generate_password_hash

def set_test_user_password():
    """Set password for the test user"""
    
    db_path = "altona_village_cms/src/database/app.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Set password for test user
    test_email = "johanvonlandsberg080808@gmai.com"
    password = "dGdFHLCJxx44ykq"
    password_hash = generate_password_hash(password)
    
    cursor.execute("UPDATE users SET password_hash = ? WHERE email = ?", (password_hash, test_email))
    rows_affected = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"✅ Updated password for {rows_affected} user accounts with email {test_email}")

if __name__ == "__main__":
    set_test_user_password()
