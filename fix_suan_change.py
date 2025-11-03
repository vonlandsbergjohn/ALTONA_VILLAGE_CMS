#!/usr/bin/env python3
import psycopg2
import os
from datetime import datetime

DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://postgres:%23Johnvonl1977@localhost:5432/altona_village_db")

conn = None
try:
    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    print("=== Fixing Suan's Test Change ===")

    # Delete the old fake test change
    cursor.execute("""
        DELETE FROM user_changes 
        WHERE user_name = 'suan vermeulen' AND field_name = 'vehicle_registration'
    """)
    print("Deleted old fake test change")

    # Create a new realistic test change that matches her actual vehicle
    cursor.execute("""
        INSERT INTO user_changes 
        (user_id, user_name, erf_number, change_type, field_name, old_value, new_value, change_timestamp, admin_reviewed)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        "e5842e2e-2617-4524-8e80-6678d0b2c404",  # suan's actual user_id
        "suan vermeulen",
        "67890",  # placeholder erf
        "vehicle_update",
        "vehicle_registration", 
        "OLD12345",  # fake old value
        "CW12345",   # her ACTUAL current vehicle (this should show red highlight)
        datetime.now(),
        False  # admin_reviewed = false
    ))

    conn.commit()
    print("✅ Created realistic test change: OLD12345 -> CW12345")
    print("Now CW12345 should appear with red highlighting in Gate Register!")

except Exception as e:
    print(f"An error occurred: {e}")
finally:
    if conn:
        conn.close()
