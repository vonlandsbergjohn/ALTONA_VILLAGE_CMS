#!/usr/bin/env python3
"""
Fix User Status from 'approved' to 'active'
This will allow the user to appear in the gate register
"""

import psycopg2
import os

DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://postgres:%23Johnvonl1977@localhost:5432/altona_village_db")

def fix_user_status():
    """Fix the user status to active"""
    
    user_id = "07b8e522-03e6-46e5-860e-2d991dfa6675"
    
    print("🔧 FIXING USER STATUS TO ACTIVE")
    print("=" * 50)
    
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Check current status
        cursor.execute("SELECT email, status, role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if user:
            print(f"Current User: {user[0]}") # type: ignore
            print(f"Current Status: {user[1]}") # type: ignore
            print(f"Current Role: {user[2]}") # type: ignore
            
            if user[1] == 'approved': # type: ignore
                # Update to active
                cursor.execute("UPDATE users SET status = 'active' WHERE id = %s", (user_id,))
                conn.commit()
                print("✅ User status updated from 'approved' to 'active'")
                
                # Verify the change
                cursor.execute("SELECT status FROM users WHERE id = %s", (user_id,))
                new_status = cursor.fetchone()[0]
                print(f"✅ Verified new status: {new_status}")
                
            else:
                print(f"User status is already: {user[1]}") # type: ignore
        else:
            print("❌ User not found!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_user_status()
