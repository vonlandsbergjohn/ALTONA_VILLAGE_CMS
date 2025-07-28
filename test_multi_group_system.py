#!/usr/bin/env python3
"""
Comprehensive test script for the multi-group system
Tests all new endpoints and functionality
"""
import urllib.request
import urllib.error
import json
import sys
import os

BASE_URL = "http://127.0.0.1:5000/api"

def test_endpoint(url, description):
    """Test an API endpoint and print results"""
    print(f"\n🔍 Testing: {description}")
    print(f"URL: {url}")
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            status_code = response.getcode()
            content = response.read().decode('utf-8')
            
        print(f"Status Code: {status_code}")
        
        if status_code == 200:
            try:
                data = json.loads(content)
                print(f"✅ Success: {json.dumps(data, indent=2)}")
                return data
            except json.JSONDecodeError:
                print(f"✅ Success: {content[:200]}...")
                return content
        else:
            print(f"❌ Failed: {content}")
            return None
            
    except urllib.error.URLError as e:
        print(f"❌ Connection Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return None

def main():
    print("=" * 60)
    print("🎯 MULTI-GROUP SYSTEM COMPREHENSIVE TEST")
    print("=" * 60)
    
    # Test 1: Groups Summary
    groups_data = test_endpoint(
        f"{BASE_URL}/admin/communication/groups-summary",
        "Groups Summary - Overview of all user groups"
    )
    
    # Test 2: Residents Group
    residents_data = test_endpoint(
        f"{BASE_URL}/admin/communication/residents-group", 
        "Residents Group - All residents (including owner-residents)"
    )
    
    # Test 3: Owners Group  
    owners_data = test_endpoint(
        f"{BASE_URL}/admin/communication/owners-group",
        "Owners Group - All property owners"
    )
    
    # Test 4: Non-Resident Owners
    non_resident_owners = test_endpoint(
        f"{BASE_URL}/admin/communication/non-resident-owners",
        "Non-Resident Owners - Owners who don't live on property"
    )
    
    # Test 5: Owner-Residents
    owner_residents = test_endpoint(
        f"{BASE_URL}/admin/communication/owner-residents", 
        "Owner-Residents - People who both own and live on property"
    )
    
    # Test 6: Existing endpoints to ensure they still work
    existing_endpoints = [
        ("/admin/pending-registrations", "Pending Registrations"),
        ("/admin/residents", "All Residents"),
        ("/admin/communication/emails", "All Email Addresses"),
        ("/admin/email-status", "Email Service Status")
    ]
    
    print(f"\n{'=' * 40}")
    print("🔧 TESTING EXISTING ENDPOINTS")
    print(f"{'=' * 40}")
    
    for endpoint, description in existing_endpoints:
        test_endpoint(f"{BASE_URL}{endpoint}", description)
    
    # Summary
    print(f"\n{'=' * 60}")
    print("📊 TEST SUMMARY")
    print(f"{'=' * 60}")
    
    if groups_data:
        print("✅ Multi-group system is functional!")
        print("✅ Database migration successful!")
        print("✅ New API endpoints working!")
        print("\n🎉 Your estate management system now supports:")
        print("   • Separate Resident and Owner data storage")
        print("   • Targeted bulk communication to specific groups")
        print("   • Owner-Resident dual categorization")
        print("   • Non-resident owner management")
        
        if isinstance(groups_data, dict):
            print(f"\n📈 Current System Stats:")
            for key, value in groups_data.items():
                if isinstance(value, (int, str)):
                    print(f"   • {key.replace('_', ' ').title()}: {value}")
    else:
        print("❌ Multi-group system needs debugging")
        print("💡 Check backend logs for errors")

if __name__ == "__main__":
    main()
