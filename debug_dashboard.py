import requests
import traceback

print("=== Debugging Dashboard Crash ===\n")

# Test backend endpoints that the dashboard uses
base_url = "http://127.0.0.1:5000/api"

print("1. Testing basic backend connectivity...")
try:
    response = requests.get(f"{base_url}/admin/gate-register", timeout=5)
    print(f"Gate Register endpoint: Status {response.status_code}")
except Exception as e:
    print(f"❌ Gate Register endpoint failed: {e}")

print("\n2. Testing new gate register changes endpoint...")
try:
    response = requests.get(f"{base_url}/admin/gate-register/changes", timeout=5)
    print(f"Gate Register Changes endpoint: Status {response.status_code}")
    if response.status_code != 200:
        print(f"Response: {response.text}")
except Exception as e:
    print(f"❌ Gate Register Changes endpoint failed: {e}")
    traceback.print_exc()

print("\n3. Testing direct database access...")
try:
    import sqlite3
    conn = sqlite3.connect('altona_village_cms/src/database/app.db')
    cursor = conn.cursor()
    
    # Test the query that the API uses
    cursor.execute("""
        SELECT DISTINCT user_id, field_name, new_value, old_value, change_timestamp
        FROM user_changes 
        WHERE admin_reviewed = 0
        ORDER BY change_timestamp DESC
        LIMIT 3
    """)
    
    changes = cursor.fetchall()
    print(f"✅ Database query works: Found {len(changes)} changes")
    for change in changes:
        print(f"  - {change[0][:8]}...: {change[1]} = {change[2]}")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Database query failed: {e}")
    traceback.print_exc()

print("\n4. Checking frontend build status...")
print("If the dashboard crashes, it's likely due to:")
print("- Import path issue with '@/lib/api'")
print("- API response format mismatch")
print("- Missing response data handling")
print("- React component state management issue")

print("\n🔍 Next step: Check browser console for specific error messages")
