#!/usr/bin/env python3
"""
Fix User Status from 'approved' to 'active'
This will allow the user to appear in the gate register
"""

import sqlite3

def fix_user_status():
    """Fix the user status to active"""
    
    db_path = r"C:\Altona_Village_CMS\altona_village_cms\src\database\app.db"
    user_id = "07b8e522-03e6-46e5-860e-2d991dfa6675"
    
    print("🔧 FIXING USER STATUS TO ACTIVE")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current status
        cursor.execute("SELECT email, status, role FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if user:
            print(f"Current User: {user[0]}")
            print(f"Current Status: {user[1]}")
            print(f"Current Role: {user[2]}")
            
            if user[1] == 'approved':
                # Update to active
                cursor.execute("UPDATE users SET status = 'active' WHERE id = ?", (user_id,))
                conn.commit()
                print("✅ User status updated from 'approved' to 'active'")
                
                # Verify the change
                cursor.execute("SELECT status FROM users WHERE id = ?", (user_id,))
                new_status = cursor.fetchone()[0]
                print(f"✅ Verified new status: {new_status}")
                
            else:
                print(f"User status is already: {user[1]}")
        else:
            print("❌ User not found!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_user_status()
