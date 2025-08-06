import sqlite3

conn = sqlite3.connect('altona_village_cms/src/database/app.db')
cursor = conn.cursor()

print("Looking for our multi-ERF test registrations:")
cursor.execute('''
    SELECT u.id, u.email, u.status, 
           COALESCE(r.erf_number, o.erf_number) as erf_number,
           COALESCE(r.first_name, o.first_name) as first_name,
           COALESCE(r.last_name, o.last_name) as last_name
    FROM users u 
    LEFT JOIN residents r ON u.id = r.user_id 
    LEFT JOIN owners o ON u.id = o.user_id
    WHERE u.email = "test.multierf@example.com" 
       OR u.email = "normal.user@example.com"
    ORDER BY u.created_at DESC
''')

for row in cursor.fetchall():
    print(f'  {row[0][:8]}...: {row[1]} - {row[2]} - ERF {row[3]} - {row[4]} {row[5]}')

# Activate them for testing
print("\nActivating these users...")
cursor.execute('UPDATE users SET status = "active" WHERE email IN ("test.multierf@example.com", "normal.user@example.com")')
conn.commit()
print(f'Updated {cursor.rowcount} users to active status')

conn.close()
