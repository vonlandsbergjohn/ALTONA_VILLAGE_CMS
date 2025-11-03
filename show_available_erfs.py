#!/usr/bin/env python3
"""
Show available ERF numbers for testing the autofill functionality.
"""

import psycopg2
import os

DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://postgres:%23Johnvonl1977@localhost:5432/altona_village_db")

def show_available_erfs():
    """Display all available ERF numbers for testing"""
    
    print("🏠 Available ERF Numbers for Testing")
    print("=" * 50)
    
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Get all ERF mappings
        cursor.execute("""
            SELECT erf_number, street_number, street_name, full_address 
            FROM erf_address_mappings 
            ORDER BY erf_number::int
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
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    show_available_erfs()
