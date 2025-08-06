import sqlite3

conn = sqlite3.connect('altona_village_cms/src/database/app.db')
cursor = conn.cursor()

print("All test users:")
cursor.execute('SELECT id, email, status FROM users WHERE email LIKE "test.%@example.com"')
for row in cursor.fetchall():
    print(f'  {row[0][:8]}...: {row[1]} - {row[2]}')

print("\nAll normal users:")
cursor.execute('SELECT id, email, status FROM users WHERE email LIKE "normal.%@example.com"')
for row in cursor.fetchall():
    print(f'  {row[0][:8]}...: {row[1]} - {row[2]}')

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
    print(f'  {row[0][:8]}...: {row[1]} - {row[2]} - ERF {row[3]}')

conn.close()
