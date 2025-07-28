import sqlite3
import os

# Change to the correct directory
os.chdir(r'c:\Altona_Village_CMS\altona_village_cms\src')

# Connect to database
conn = sqlite3.connect('database/app.db')
cursor = conn.cursor()

# Check table structure first
cursor.execute('PRAGMA table_info(users)')
columns = cursor.fetchall()
print("Users table columns:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# Get a non-admin user
cursor.execute('SELECT * FROM users WHERE role != "admin" LIMIT 1')
user = cursor.fetchone()
print(f"\nFirst user record: {user}")

conn.close()
