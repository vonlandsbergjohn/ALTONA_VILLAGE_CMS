#!/usr/bin/env python3
import sqlite3
from datetime import datetime

# Connect to database
db_path = 'altona_village_cms/src/database/app.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== Fixing Suan's Test Change ===")

# Delete the old fake test change
cursor.execute('''
    DELETE FROM user_changes 
    WHERE user_name = "suan vermeulen" AND field_name = "vehicle_registration"
''')
print("Deleted old fake test change")

# Create a new realistic test change that matches her actual vehicle
cursor.execute('''
    INSERT INTO user_changes 
    (user_id, user_name, erf_number, change_type, field_name, old_value, new_value, change_timestamp, admin_reviewed)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    "e5842e2e-2617-4524-8e80-6678d0b2c404",  # suan's actual user_id
    "suan vermeulen",
    "67890",  # placeholder erf
    "vehicle_update",
    "vehicle_registration", 
    "OLD12345",  # fake old value
    "CW12345",   # her ACTUAL current vehicle (this should show red highlight)
    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    0  # admin_reviewed = false
))

conn.commit()
print("✅ Created realistic test change: OLD12345 -> CW12345")
print("Now CW12345 should appear with red highlighting in Gate Register!")

conn.close()
