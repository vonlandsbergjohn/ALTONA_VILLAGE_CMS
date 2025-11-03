#!/usr/bin/env python3
"""
Fix residents table schema - add missing columns
"""

import psycopg2
import os

DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://postgres:%23Johnvonl1977@localhost:5432/altona_village_db")

def fix_residents_schema():
    """Add missing columns to residents table"""
    
    print("🔧 Fixing Residents Table Schema")
    print("=" * 40)
    
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Check current columns for residents
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'residents'")
        current_columns = [row[0] for row in cursor.fetchall()]
        print(f"Current residents columns: {current_columns}")
        
        # Add missing columns to residents
        missing_columns = [
            ("moving_in_date", "DATE"),
            ("moving_out_date", "DATE"),
            ("status", "VARCHAR(20)", "active"),
            ("migration_date", "TIMESTAMP"),
            ("migration_reason", "TEXT")
        ]
        
        for column_info in missing_columns:
            column_name, column_type, default_value = (column_info + [None])[:3]
            
            if column_name not in current_columns:
                try:
                    sql = f"ALTER TABLE residents ADD COLUMN {column_name} {column_type}"
                    if default_value:
                        sql += f" DEFAULT '{default_value}'"
                    cursor.execute(sql)
                    print(f"✅ Added column to residents: {column_name} ({column_type})")
                except psycopg2.Error as e:
                    print(f"❌ Error adding {column_name} to residents: {e}")
                    conn.rollback()
            else:
                print(f"⚪ Column {column_name} already exists in residents")
        
        # Also check owners table
        print("\n🔧 Checking Owners Table Schema")
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'owners'")
        owner_columns = [row[0] for row in cursor.fetchall()]
        print(f"Owner columns: {owner_columns}")
        
        # Add missing columns to owners table too
        for column_info in missing_columns:
            column_name, column_type, default_value = (column_info + [None])[:3]
            
            if column_name not in owner_columns:
                try:
                    sql = f"ALTER TABLE owners ADD COLUMN {column_name} {column_type}"
                    if default_value:
                        sql += f" DEFAULT '{default_value}'"
                    cursor.execute(sql)
                    print(f"✅ Added column to owners: {column_name} ({column_type})")
                except psycopg2.Error as e:
                    print(f"❌ Error adding {column_name} to owners: {e}")
                    conn.rollback()
            else:
                print(f"⚪ Column {column_name} already exists in owners")
        
        conn.commit()
        print("\n✅ Schema fix complete!")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_residents_schema()
