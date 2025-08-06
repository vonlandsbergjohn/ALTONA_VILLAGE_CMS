import sqlite3

conn = sqlite3.connect('altona_village_cms/src/database/app.db')
cursor = conn.cursor()

# Activate the test multi-ERF users
cursor.execute('UPDATE users SET status = "active" WHERE email = "test.multierf@example.com"')
conn.commit()
print(f'Updated {cursor.rowcount} users to active status')

# Check the results
cursor.execute('SELECT id, email, status FROM users WHERE email = "test.multierf@example.com"')
for row in cursor.fetchall():
    print(f'  {row[0][:8]}...: {row[1]} - {row[2]}')

# Check if they have owner records
cursor.execute('''
    SELECT u.email, o.erf_number, o.full_address, o.first_name, o.last_name 
    FROM users u 
    JOIN owners o ON u.id = o.user_id 
    WHERE u.email = "test.multierf@example.com"
''')

print('\nOwner records:')
for row in cursor.fetchall():
    print(f'  ERF {row[1]}: {row[3]} {row[4]} - {row[2]}')

conn.close()
