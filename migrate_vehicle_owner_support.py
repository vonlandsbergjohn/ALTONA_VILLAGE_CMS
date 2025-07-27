#!/usr/bin/env python3

"""
Database Migration: Add owner_id support to Vehicle model
This migration adds owner_id column to vehicles table to support owner vehicles
"""

import sqlite3
import sys
import os

# Add the project directory to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def migrate_database():
    db_path = os.path.join(project_root, 'altona_village_cms', 'src', 'database', 'app.db')
    
    if not os.path.exists(db_path):
        print(f"Database file not found at: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Starting vehicle owner support migration...")
        
        # Check if owner_id column already exists
        cursor.execute("PRAGMA table_info(vehicles)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'owner_id' not in columns:
            print("Adding owner_id column to vehicles table...")
            cursor.execute('''
                ALTER TABLE vehicles 
                ADD COLUMN owner_id TEXT REFERENCES owners(id)
            ''')
            
            # Make resident_id nullable (it was originally NOT NULL)
            print("Updating vehicles table schema to allow nullable resident_id...")
            
            # Create new table with correct schema
            cursor.execute('''
                CREATE TABLE vehicles_new (
                    id TEXT PRIMARY KEY,
                    resident_id TEXT REFERENCES residents(id),
                    owner_id TEXT REFERENCES owners(id),
                    registration_number TEXT UNIQUE NOT NULL,
                    make TEXT,
                    model TEXT,
                    color TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Copy data from old table
            cursor.execute('''
                INSERT INTO vehicles_new (id, resident_id, registration_number, make, model, color, created_at, updated_at)
                SELECT id, resident_id, registration_number, make, model, color, created_at, updated_at
                FROM vehicles
            ''')
            
            # Drop old table and rename new one
            cursor.execute('DROP TABLE vehicles')
            cursor.execute('ALTER TABLE vehicles_new RENAME TO vehicles')
            
            print("✅ Successfully added owner_id support to vehicles table")
        else:
            print("✅ owner_id column already exists in vehicles table")
        
        # Verify the migration
        cursor.execute("PRAGMA table_info(vehicles)")
        columns_after = cursor.fetchall()
        print(f"Vehicles table columns after migration: {[col[1] for col in columns_after]}")
        
        conn.commit()
        print("✅ Migration completed successfully!")
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
    print("=== Vehicle Owner Support Migration ===")
    success = migrate_database()
    if success:
        print("Migration completed successfully! Owners can now register vehicles.")
    else:
        print("Migration failed. Please check the error messages above.")
        sys.exit(1)
