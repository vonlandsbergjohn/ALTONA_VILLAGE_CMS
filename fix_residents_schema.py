#!/usr/bin/env python3
"""
Fix residents table schema - add missing columns
"""

import sqlite3
from datetime import datetime

def fix_residents_schema():
    """Add missing columns to residents table"""
    
    db_path = "altona_village_cms/src/database/app.db"
    
    print("🔧 Fixing Residents Table Schema")
    print("=" * 40)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check current columns
    cursor.execute("PRAGMA table_info(residents)")
    current_columns = [row[1] for row in cursor.fetchall()]
    print(f"Current columns: {current_columns}")
    
    # Add missing columns
    missing_columns = [
        ("moving_in_date", "DATE"),
        ("moving_out_date", "DATE"),
        ("status", "VARCHAR(20)", "active"),
        ("migration_date", "DATETIME"),
        ("migration_reason", "TEXT")
    ]
    
    for column_info in missing_columns:
        column_name = column_info[0]
        column_type = column_info[1]
        default_value = column_info[2] if len(column_info) > 2 else None
        
        if column_name not in current_columns:
            try:
                if default_value:
                    sql = f"ALTER TABLE residents ADD COLUMN {column_name} {column_type} DEFAULT '{default_value}'"
                else:
                    sql = f"ALTER TABLE residents ADD COLUMN {column_name} {column_type}"
                
                cursor.execute(sql)
                print(f"✅ Added column: {column_name} ({column_type})")
            except sqlite3.Error as e:
                print(f"❌ Error adding {column_name}: {e}")
        else:
            print(f"⚪ Column {column_name} already exists")
    
    # Also check owners table
    print("\n🔧 Checking Owners Table Schema")
    cursor.execute("PRAGMA table_info(owners)")
    owner_columns = [row[1] for row in cursor.fetchall()]
    print(f"Owner columns: {owner_columns}")
    
    # Add missing columns to owners table too
    for column_info in missing_columns:
        column_name = column_info[0]
        column_type = column_info[1]
        default_value = column_info[2] if len(column_info) > 2 else None
        
        if column_name not in owner_columns:
            try:
                if default_value:
                    sql = f"ALTER TABLE owners ADD COLUMN {column_name} {column_type} DEFAULT '{default_value}'"
                else:
                    sql = f"ALTER TABLE owners ADD COLUMN {column_name} {column_type}"
                
                cursor.execute(sql)
                print(f"✅ Added column to owners: {column_name} ({column_type})")
            except sqlite3.Error as e:
                print(f"❌ Error adding {column_name} to owners: {e}")
        else:
            print(f"⚪ Column {column_name} already exists in owners")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Schema fix complete!")

if __name__ == "__main__":
    fix_residents_schema()
