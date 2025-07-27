#!/usr/bin/env python3
"""
Database migration script to add intercom_code field to residents and owners tables
"""

import sqlite3
import os
import sys
from datetime import datetime

def run_migration():
    """Add intercom_code column to residents and owners tables"""
    db_path = os.path.join(os.path.dirname(__file__), 'altona_village_cms', 'src', 'database', 'app.db')
    
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return False
    
    print(f"Running migration on database: {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if intercom_code column already exists in residents table
        cursor.execute("PRAGMA table_info(residents)")
        residents_columns = [column[1] for column in cursor.fetchall()]
        
        if 'intercom_code' not in residents_columns:
            print("Adding intercom_code column to residents table...")
            cursor.execute("""
                ALTER TABLE residents 
                ADD COLUMN intercom_code VARCHAR(20)
            """)
            print("✓ intercom_code column added to residents table")
        else:
            print("⚠ intercom_code column already exists in residents table")
        
        # Check if intercom_code column already exists in owners table
        cursor.execute("PRAGMA table_info(owners)")
        owners_columns = [column[1] for column in cursor.fetchall()]
        
        if 'intercom_code' not in owners_columns:
            print("Adding intercom_code column to owners table...")
            cursor.execute("""
                ALTER TABLE owners 
                ADD COLUMN intercom_code VARCHAR(20)
            """)
            print("✓ intercom_code column added to owners table")
        else:
            print("⚠ intercom_code column already exists in owners table")
        
        # Commit the changes
        conn.commit()
        print(f"✅ Migration completed successfully at {datetime.now()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🔄 Starting intercom_code migration...")
    success = run_migration()
    sys.exit(0 if success else 1)
