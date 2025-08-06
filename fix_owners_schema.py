#!/usr/bin/env python3
"""
Fix the owners table schema by adding missing columns.
"""

import sqlite3

def fix_owners_schema():
    """Add missing columns to the owners table"""
    
    db_path = "altona_village_cms/src/database/app.db"
    
    print("🔧 Fixing Owners Table Schema")
    print("=" * 40)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # List of missing columns to add
    missing_columns = [
        ("acquisition_date", "DATE"),
        ("postal_street_number", "VARCHAR(10)"),
        ("postal_street_name", "VARCHAR(200)"),
        ("postal_suburb", "VARCHAR(100)"),
        ("postal_city", "VARCHAR(100)"),
        ("postal_code", "VARCHAR(10)"),
        ("postal_province", "VARCHAR(100)")
    ]
    
    for column_name, column_type in missing_columns:
        try:
            # Check if column exists
            cursor.execute(f"PRAGMA table_info(owners)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if column_name not in columns:
                print(f"➕ Adding column: {column_name} ({column_type})")
                cursor.execute(f"ALTER TABLE owners ADD COLUMN {column_name} {column_type}")
            else:
                print(f"✅ Column exists: {column_name}")
                
        except Exception as e:
            print(f"❌ Error adding {column_name}: {e}")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print("\n✅ Owners table schema update completed!")
    
    # Verify the schema
    print("\n🔍 Verifying owners table schema:")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(owners)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} - {col[2]}")
    conn.close()

if __name__ == "__main__":
    fix_owners_schema()
