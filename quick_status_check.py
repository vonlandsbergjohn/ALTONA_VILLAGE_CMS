import psycopg2
import os

DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://postgres:%23Johnvonl1977@localhost:5432/altona_village_db")

conn = None
try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, erf_number, status, migration_completed, new_user_id
        FROM user_transition_requests 
        WHERE erf_number = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, ('27727',))

    transition = cursor.fetchone()
    if transition:
        print('CURRENT TRANSITION STATUS:')
        print(f'  ID: {transition[0]}')
        print(f'  ERF: {transition[1]}')
        print(f'  Status: {transition[2]}')
        print(f'  Migration Completed: {transition[3]}')
        print(f'  New User ID: {transition[4]}')
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    if conn:
        conn.close()
