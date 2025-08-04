import sqlite3

conn = sqlite3.connect(r"C:\Altona_Village_CMS\altona_village_cms\src\database\app.db")
cursor = conn.cursor()

cursor.execute("""
    SELECT id, erf_number, status, request_type, 
           new_occupant_first_name, new_occupant_last_name, new_occupant_type,
           migration_completed, new_user_id
    FROM user_transition_requests 
    WHERE erf_number = '27727'
    ORDER BY created_at DESC
    LIMIT 1
""")

transition = cursor.fetchone()
if transition:
    print('LATEST TRANSITION REQUEST:')
    print(f'  ID: {transition[0]}')
    print(f'  ERF: {transition[1]}')
    print(f'  Status: {transition[2]}')
    print(f'  Type: {transition[3]}')
    print(f'  Expected New Occupant: {transition[4]} {transition[5]} ({transition[6]})')
    print(f'  Migration Completed: {transition[7]}')
    print(f'  New User ID: {transition[8]}')

conn.close()
