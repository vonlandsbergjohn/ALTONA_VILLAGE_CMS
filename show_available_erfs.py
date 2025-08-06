#!/usr/bin/env python3
"""
Show available ERF numbers for testing the autofill functionality.
"""

import sqlite3

def show_available_erfs():
    """Display all available ERF numbers for testing"""
    
    db_path = "altona_village_cms/src/database/app.db"
    
    print("🏠 Available ERF Numbers for Testing")
    print("=" * 50)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all ERF mappings
    cursor.execute("""
        SELECT erf_number, street_number, street_name, full_address 
        FROM erf_address_mappings 
        ORDER BY CAST(erf_number AS INTEGER)
    """)
    erfs = cursor.fetchall()
    
    print(f"📍 Available ERFs ({len(erfs)} total):")
    print("\nFor testing ERF autofill, try these numbers:")
    for erf in erfs:
        print(f"  ERF {erf[0]}: {erf[1]} {erf[2]}")
    
    print(f"\n🧪 Test Instructions:")
    print("1. Go to the registration form")
    print("2. Enter one of the ERF numbers above (e.g., 27627)")
    print("3. Press Enter or click away from the ERF field")
    print("4. The street number and name should auto-populate")
    
    print(f"\n⚠️  Note: ERF 27727 (from your screenshot) is NOT in the database")
    print("   That's why the autofill didn't work!")
    
    conn.close()

if __name__ == "__main__":
    show_available_erfs()
