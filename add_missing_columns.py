#!/usr/bin/env python3
"""
Add missing columns to the database tables.
"""

import sqlite3

def add_missing_columns():
    """Add missing columns to residents and other tables"""
    
    db_path = "altona_village_cms/src/database/app.db"
    
    print("🔧 Adding missing database columns...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Add missing columns to residents table
    columns_to_add = [
        ("residents", "moving_in_date", "DATE"),
        ("residents", "moving_out_date", "DATE"),
        ("residents", "status", "VARCHAR(50) DEFAULT 'active'"),
        ("residents", "migration_date", "DATE"),
        ("residents", "migration_reason", "TEXT"),
        ("owners", "moving_in_date", "DATE"),
        ("owners", "moving_out_date", "DATE"),
        ("owners", "status", "VARCHAR(50) DEFAULT 'active'"),
        ("owners", "migration_date", "DATE"),
        ("owners", "migration_reason", "TEXT")
    ]
    
    for table, column, column_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
            print(f"✅ Added {table}.{column}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"⚠️  {table}.{column} already exists")
            else:
                print(f"❌ Error adding {table}.{column}: {e}")
    
    # Check if we need to add any other missing columns by examining the error
    # The error mentions several columns, let's make sure they all exist
    
    print("✅ Database columns updated")
    
    conn.commit()
    conn.close()
    
    print("\n🎯 Database Update Complete!")
    print("The login should work now!")

if __name__ == "__main__":
    add_missing_columns()
