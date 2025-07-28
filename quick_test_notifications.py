import requests
import json

# Simple test of admin notification endpoints
BASE_URL = "http://127.0.0.1:5000/api"

print("🔧 Quick Admin Notification API Test")
print("=" * 40)

# Test without authentication first to see if endpoints exist
print("Testing endpoint availability...")

endpoints = [
    "/admin/changes/stats",
    "/admin/changes/pending", 
    "/admin/changes/critical",
    "/admin/changes/export-critical?type=accentronix"
]

for endpoint in endpoints:
    try:
        response = requests.get(f"{BASE_URL}{endpoint}")
        if response.status_code == 403:
            print(f"✅ {endpoint} - Endpoint exists (requires auth)")
        elif response.status_code == 404:
            print(f"❌ {endpoint} - Endpoint not found")
        else:
            print(f"📝 {endpoint} - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ {endpoint} - Connection error: {str(e)}")

print("\n🎯 Summary:")
print("If you see 'requires auth' messages, the system is working!")
print("Access the admin dashboard at: http://localhost:5174/admin/notifications")
