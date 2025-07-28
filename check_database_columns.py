#!/usr/bin/env python3
"""
Check if intercom_code columns exist in the database
"""

import sqlite3
import os

def check_database_columns():
    """Check if intercom_code columns exist in residents and owners tables"""
    db_path = os.path.join(os.path.dirname(__file__), 'altona_village_cms', 'src', 'database', 'app.db')
    
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return False
    
    print(f"Checking database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check residents table
        print("\n=== RESIDENTS TABLE ===")
        cursor.execute("PRAGMA table_info(residents)")
        residents_columns = cursor.fetchall()
        
        intercom_found_residents = False
        for column in residents_columns:
            if column[1] == 'intercom_code':
                print(f"✓ intercom_code column found: {column}")
                intercom_found_residents = True
            elif 'intercom' in column[1].lower():
                print(f"Related column: {column}")
        
        if not intercom_found_residents:
            print("❌ intercom_code column NOT found in residents table")
        
        # Check owners table
        print("\n=== OWNERS TABLE ===")
        cursor.execute("PRAGMA table_info(owners)")
        owners_columns = cursor.fetchall()
        
        intercom_found_owners = False
        for column in owners_columns:
            if column[1] == 'intercom_code':
                print(f"✓ intercom_code column found: {column}")
                intercom_found_owners = True
            elif 'intercom' in column[1].lower():
                print(f"Related column: {column}")
        
        if not intercom_found_owners:
            print("❌ intercom_code column NOT found in owners table")
        
        # Test data query
        print("\n=== TEST DATA QUERY ===")
        try:
            cursor.execute("SELECT id, first_name, last_name, intercom_code FROM residents LIMIT 3")
            residents_data = cursor.fetchall()
            print("Sample residents data:")
            for row in residents_data:
                print(f"  {row}")
        except sqlite3.OperationalError as e:
            print(f"❌ Error querying residents intercom_code: {e}")
        
        try:
            cursor.execute("SELECT id, first_name, last_name, intercom_code FROM owners LIMIT 3")
            owners_data = cursor.fetchall()
            print("Sample owners data:")
            for row in owners_data:
                print(f"  {row}")
        except sqlite3.OperationalError as e:
            print(f"❌ Error querying owners intercom_code: {e}")
        
        return intercom_found_residents and intercom_found_owners
        
    except Exception as e:
        print(f"❌ Error checking database: {str(e)}")
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🔍 Checking database columns...")
    success = check_database_columns()
    if success:
        print("\n✅ Database columns check passed!")
    else:
        print("\n❌ Database columns check failed!")
