#!/usr/bin/env python3
"""
Update admin user password to the correct one.
"""

import sqlite3
from werkzeug.security import generate_password_hash

def update_admin_password():
    """Set the admin user password to the correct one"""
    
    db_path = "altona_village_cms/src/database/app.db"
    
    print("🔧 Updating Admin Password")
    print("=" * 30)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check current admin user
    cursor.execute("SELECT id, email, role FROM users WHERE email = 'vonlandsbergjohn@gmail.com'")
    admin = cursor.fetchone()
    
    if admin:
        print(f"Found admin: {admin[1]}")
        
        # Set password to the correct one
        correct_password = "dGdFHLCJxx44ykq"
        password_hash = generate_password_hash(correct_password)
        
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, admin[0]))
        conn.commit()
        
        print(f"✅ Admin password updated to: {correct_password}")
        print(f"✅ Email: {admin[1]}")
    else:
        print("❌ No admin user found")
    
    conn.close()

if __name__ == "__main__":
    update_admin_password()
