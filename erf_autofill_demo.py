"""
Demo script showing how the ERF address mapping system works
This demonstrates the auto-fill functionality for forms
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:5000"  # Adjust if your backend runs on different port
ERF_TO_TEST = "27727"  # Real ERF number from your system

def test_erf_lookup():
    """Test the ERF address lookup functionality"""
    print(f"🔍 Testing ERF lookup for ERF {ERF_TO_TEST}...")
    
    try:
        # Test the public API endpoint (no authentication required)
        response = requests.get(f"{BASE_URL}/api/public/lookup-address/{ERF_TO_TEST}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ ERF lookup successful!")
            print(f"   📍 Street Number: {data['street_number']}")
            print(f"   🛣️  Street Name: {data['street_name']}")
            print(f"   🏠 Full Address: {data['street_number']} {data['street_name']}")
            return data
        elif response.status_code == 404:
            print(f"❌ ERF {ERF_TO_TEST} not found in address mapping database")
            print("   💡 Tip: Upload address mappings through admin panel first")
            return None
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server")
        print("   💡 Make sure the Flask backend is running on http://localhost:5000")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def demo_form_autofill():
    """Demonstrate how auto-fill would work in a form"""
    print("\n📝 Demo: How auto-fill works in forms...")
    
    # Simulate getting ERF from user input
    erf_number = ERF_TO_TEST
    print(f"   User enters ERF: {erf_number}")
    
    # Look up address
    address_data = test_erf_lookup()
    
    if address_data:
        print("\n   🎯 Auto-fill would populate these fields:")
        print(f"   Street Number field: '{address_data['street_number']}'")
        print(f"   Street Name field: '{address_data['street_name']}'")
        print("\n   ✨ User doesn't need to type the address manually!")
    else:
        print("\n   ⚠️  No auto-fill available - user must enter address manually")

def check_server_status():
    """Check if the backend server is running"""
    print("🔧 Checking server status...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/public/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend server is running")
            return True
        else:
            print(f"⚠️  Server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend server is not running")
        print("   💡 Start the server with: python altona_village_cms/src/main.py")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {e}")
        return False

if __name__ == "__main__":
    print("🏘️  Altona Village CMS - ERF Address Auto-Fill Demo")
    print("=" * 50)
    
    # Check if server is running
    if not check_server_status():
        print("\n💡 To start the backend server:")
        print("   1. cd altona_village_cms")
        print("   2. python src/main.py")
        print("   3. Or use VS Code task: 'Start Backend'")
        exit(1)
    
    print("\n" + "=" * 50)
    
    # Test ERF lookup
    test_erf_lookup()
    
    print("\n" + "=" * 50)
    
    # Demo form auto-fill
    demo_form_autofill()
    
    print("\n" + "=" * 50)
    print("📋 Summary:")
    print("• ERF address mapping allows centralized address management")
    print("• Auto-fill reduces data entry errors and saves time")
    print("• Public API endpoint works without authentication")
    print("• Frontend components can easily integrate auto-fill functionality")
    print(f"• Test with different ERF numbers by changing ERF_TO_TEST variable")
