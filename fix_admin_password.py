#!/usr/bin/env python3
"""
Fix admin user password.
"""

import sqlite3
from werkzeug.security import generate_password_hash

def fix_admin_password():
    """Set the admin user password"""
    
    db_path = "altona_village_cms/src/database/app.db"
    
    print("🔧 Fixing Admin Password")
    print("=" * 30)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check current admin user
    cursor.execute("SELECT id, email, role, password_hash FROM users WHERE role = 'admin'")
    admin = cursor.fetchone()
    
    if admin:
        print(f"Found admin: {admin[1]}")
        
        # Set password to 'admin123'
        new_password = "admin123"
        password_hash = generate_password_hash(new_password)
        
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, admin[0]))
        conn.commit()
        
        print(f"✅ Admin password updated to: {new_password}")
    else:
        print("❌ No admin user found")
    
    conn.close()

if __name__ == "__main__":
    fix_admin_password()
