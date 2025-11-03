import psycopg2
import os

# Use the same database URL as the main application
DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://postgres:%23Johnvonl1977@localhost:5432/altona_village_db")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, erf_number, status, request_type, 
               new_occupant_first_name, new_occupant_last_name, new_occupant_type,
               migration_completed, new_user_id
        FROM user_transition_requests 
        WHERE erf_number = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, ('27727',))

    transition = cursor.fetchone()
    if transition:
        print('LATEST TRANSITION REQUEST:')
        print(f'  ID: {transition[0]}')
        print(f'  ERF: {transition[1]}')
        print(f'  Status: {transition[2]}')
        print(f'  Request Type: {transition[3]}')
        print(f'  New Occupant: {transition[4]} {transition[5]} ({transition[6]})') # type: ignore
        print(f'  Migration Completed: {transition[7]}')
        print(f'  New User ID: {transition[8]}')
    else:
        print("No transition request found for ERF '27727'.")

    conn.close()
except Exception as e:
    print(f"Error connecting to the database: {e}")
