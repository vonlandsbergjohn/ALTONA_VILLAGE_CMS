import sqlite3

conn = sqlite3.connect(r"C:\Altona_Village_CMS\altona_village_cms\src\database\app.db")
cursor = conn.cursor()

cursor.execute("""
    SELECT id, erf_number, status, migration_completed, new_user_id
    FROM user_transition_requests 
    WHERE erf_number = '27727'
    ORDER BY created_at DESC
    LIMIT 1
""")

transition = cursor.fetchone()
if transition:
    print('CURRENT TRANSITION STATUS:')
    print(f'  ID: {transition[0]}')
    print(f'  ERF: {transition[1]}')
    print(f'  Status: {transition[2]}')
    print(f'  Migration Completed: {transition[3]}')
    print(f'  New User ID: {transition[4]}')

conn.close()
