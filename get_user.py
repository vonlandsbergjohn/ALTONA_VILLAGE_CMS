import psycopg2
import os

DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://postgres:%23Johnvonl1977@localhost:5432/altona_village_db")

conn = None
try:
    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Check table structure first
    cursor.execute("""
        SELECT column_name, data_type FROM information_schema.columns
        WHERE table_name = 'users'
    """)
    columns = cursor.fetchall()
    print("Users table columns:")
    for col in columns:
        print(f"  {col[0]} ({col[1]})")

    # Get a non-admin user
    cursor.execute("SELECT * FROM users WHERE role <> 'admin' LIMIT 1")
    user = cursor.fetchone()
    print(f"\nFirst user record: {user}")

except Exception as e:
    print(f"An error occurred: {e}")
finally:
    if conn:
        conn.close()
