import psycopg2
import os

DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://postgres:%23Johnvonl1977@localhost:5432/altona_village_db")

conn = None
try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    print("All test users:")
    cursor.execute("SELECT id, email, status FROM users WHERE email LIKE 'test.%%@example.com'")
    for row in cursor.fetchall():
        print(f'  {str(row[0])[:8]}...: {row[1]} - {row[2]}')

    print("\nAll normal users:")
    cursor.execute("SELECT id, email, status FROM users WHERE email LIKE 'normal.%%@example.com'")
    for row in cursor.fetchall():
        print(f'  {str(row[0])[:8]}...: {row[1]} - {row[2]}')

    # Let's activate an existing user with ERF data for testing
    print("\nUsers with ERF data (we can test with these):")
    cursor.execute('''
        SELECT u.id, u.email, u.status, r.erf_number 
        FROM users u 
        LEFT JOIN residents r ON u.id = r.user_id 
        WHERE r.erf_number IS NOT NULL
        LIMIT 5
    ''')
    for row in cursor.fetchall():
        print(f'  {str(row[0])[:8]}...: {row[1]} - {row[2]} - ERF {row[3]}')

except Exception as e:
    print(f"An error occurred: {e}")
finally:
    if conn:
        conn.close()
