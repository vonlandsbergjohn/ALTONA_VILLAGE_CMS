import requests
import json

# Test the gate register API
url = "http://localhost:5000/api/admin/gate-register"

# First, let's try to login to get a token
login_url = "http://localhost:5000/api/auth/login"

# Try different login combinations
login_attempts = [
    {"email": "vonlandsbergjohn@gmail.com", "password": "admin123"},
    {"email": "vonlandsbergjohn@gmail.com", "password": "password"},
    {"email": "admin@altona.com", "password": "admin123"},
    {"email": "admin@example.com", "password": "admin123"},
]

token = None
for creds in login_attempts:
    try:
        response = requests.post(login_url, json=creds)
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print(f"✅ Login successful with {creds['email']}")
            print(f"Token: {token[:50]}...")
            break
        else:
            print(f"❌ Login failed for {creds['email']}: {response.json()}")
    except Exception as e:
        print(f"❌ Error logging in with {creds['email']}: {e}")

if token:
    # Test the gate register API
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers)
        print(f"\n🔍 Gate Register API Response:")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success', 'N/A')}")
            print(f"Count: {data.get('count', 'N/A')}")
            print(f"Data entries: {len(data.get('data', []))}")
            
            # Show first few entries
            if data.get('data'):
                print("\n📋 First few entries:")
                for i, entry in enumerate(data['data'][:3]):
                    print(f"  {i+1}. {entry.get('resident_status', 'N/A')} - {entry.get('first_name', '')} {entry.get('last_name', '')} - Vehicles: {len(entry.get('vehicle_registrations', []))}")
        else:
            print(f"Error: {response.json()}")
    except Exception as e:
        print(f"❌ Error testing gate register: {e}")
else:
    print("❌ Could not obtain authentication token")
