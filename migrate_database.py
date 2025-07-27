#!/usr/bin/env python3
"""
Database migration script to add missing columns to residents table
"""
import os
import sqlite3
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'altona_village_cms', 'src'))

def migrate_database():
    """Add missing columns to the residents table"""
    
    # Database path
    db_path = os.path.join(os.path.dirname(__file__), 'altona_village_cms', 'src', 'database', 'app.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current table structure
        cursor.execute("PRAGMA table_info(residents)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Current columns in residents table: {columns}")
        
        # Add missing columns if they don't exist
        new_columns = [
            ('id_number', 'VARCHAR(50) NOT NULL DEFAULT ""'),
            ('erf_number', 'VARCHAR(50) NOT NULL DEFAULT ""'),
            ('address', 'VARCHAR(255) NOT NULL DEFAULT ""')
        ]
        
        for column_name, column_def in new_columns:
            if column_name not in columns:
                try:
                    sql = f"ALTER TABLE residents ADD COLUMN {column_name} {column_def};"
                    print(f"Adding column: {sql}")
                    cursor.execute(sql)
                    print(f"✅ Added column {column_name}")
                except Exception as e:
                    print(f"❌ Error adding column {column_name}: {e}")
            else:
                print(f"✅ Column {column_name} already exists")
        
        # Commit changes
        conn.commit()
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(residents)")
        updated_columns = [row[1] for row in cursor.fetchall()]
        print(f"Updated columns in residents table: {updated_columns}")
        
        conn.close()
        print("✅ Database migration completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting database migration...")
    success = migrate_database()
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")
        sys.exit(1)
