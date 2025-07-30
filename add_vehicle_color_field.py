#!/usr/bin/env python3
"""
Add color field to transition_vehicles table
"""

import sqlite3
import os

DATABASE_PATH = os.path.join('altona_village_cms', 'src', 'database', 'app.db')

def add_color_field():
    """Add color field to transition_vehicles table"""
    print("🔄 Adding color field to transition_vehicles table...")
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if color field already exists
        cursor.execute("PRAGMA table_info(transition_vehicles)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'color' not in columns:
            cursor.execute('ALTER TABLE transition_vehicles ADD COLUMN color VARCHAR(50)')
            conn.commit()
            print("   ✅ Added color field to transition_vehicles")
        else:
            print("   ℹ️  color field already exists in transition_vehicles")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to add color field: {e}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = add_color_field()
    if success:
        print("✅ Successfully added color field")
    else:
        print("❌ Failed to add color field")
        exit(1)
