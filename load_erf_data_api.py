#!/usr/bin/env python3

import requests
import json
import csv

def load_erf_data_via_api():
    """Load ERF data using the admin API"""
    
    base_url = "http://localhost:5000/api"
    
    # Admin credentials
    admin_email = "vonlandsbergjohn@gmail.com"
    admin_password = "dGdFHLCJxx44ykq"
    
    print("=== Loading ERF Data via Admin API ===\n")
    
    # Step 1: Login as admin
    print("1. Logging in as admin...")
    admin_login_data = {
        "email": admin_email,
        "password": admin_password
    }
    
    try:
        response = requests.post(f"{base_url}/auth/login", json=admin_login_data)
        if response.status_code == 200:
            admin_token = response.json()['access_token']
            print("   ✅ Admin login successful")
        else:
            print(f"   ❌ Admin login failed: {response.text}")
            return
    except Exception as e:
        print(f"   ❌ Admin login error: {e}")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Step 2: Check current ERF mappings
    print("\n2. Checking current ERF mappings...")
    try:
        response = requests.get(f"{base_url}/admin/address-mappings", headers=headers)
        if response.status_code == 200:
            current_mappings = response.json()
            print(f"   Current mappings: {len(current_mappings)}")
        else:
            print(f"   Could not get current mappings: {response.text}")
            current_mappings = []
    except Exception as e:
        print(f"   Error getting mappings: {e}")
        current_mappings = []
    
    # Step 3: Load sample data
    print("\n3. Loading sample ERF data...")
    
    sample_data = [
        {"erf_number": "27727", "street_number": "15", "street_name": "Oak Avenue"},
        {"erf_number": "27728", "street_number": "17", "street_name": "Oak Avenue"},
        {"erf_number": "27729", "street_number": "19", "street_name": "Oak Avenue"},
        {"erf_number": "27730", "street_number": "21", "street_name": "Oak Avenue"},
        {"erf_number": "27731", "street_number": "23", "street_name": "Oak Avenue"},
        {"erf_number": "27732", "street_number": "25", "street_name": "Oak Avenue"},
        {"erf_number": "27800", "street_number": "1", "street_name": "Pine Street"},
        {"erf_number": "27801", "street_number": "3", "street_name": "Pine Street"},
        {"erf_number": "27802", "street_number": "5", "street_name": "Pine Street"},
        {"erf_number": "1", "street_number": "10", "street_name": "Main Road"},
        {"erf_number": "2", "street_number": "12", "street_name": "Main Road"},
        {"erf_number": "123", "street_number": "5", "street_name": "Garden Street"},
    ]
    
    success_count = 0
    for mapping in sample_data:
        erf = mapping["erf_number"]
        street_num = mapping["street_number"]
        street_name = mapping["street_name"]
        
        mapping_data = {
            "erf_number": erf,
            "street_number": street_num,
            "street_name": street_name,
            "full_address": f"{street_num} {street_name}",
            "suburb": "Altona Village",
            "postal_code": "6850"
        }
        
        try:
            response = requests.post(f"{base_url}/admin/address-mappings", 
                                   json=mapping_data, headers=headers)
            if response.status_code == 201:
                print(f"   ✅ Added ERF {erf}: {street_num} {street_name}")
                success_count += 1
            else:
                try:
                    error_data = response.json()
                    if "already exists" in error_data.get('error', ''):
                        print(f"   ℹ️ ERF {erf} already exists")
                    else:
                        print(f"   ❌ Failed to add ERF {erf}: {error_data.get('error')}")
                except:
                    print(f"   ❌ Failed to add ERF {erf}: {response.text}")
        except Exception as e:
            print(f"   ❌ Error adding ERF {erf}: {e}")
    
    print(f"\n✅ Successfully added {success_count} ERF mappings!")
    
    # Step 4: Test the lookup functionality
    print("\n4. Testing ERF lookup functionality...")
    test_erfs = ['27727', '1', '123']
    
    for erf in test_erfs:
        try:
            response = requests.get(f"{base_url}/public/erf-lookup/{erf}")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    address_data = data['data']
                    print(f"   ✅ ERF {erf}: {address_data['street_number']} {address_data['street_name']}")
                else:
                    print(f"   ❌ ERF {erf}: {data.get('message')}")
            else:
                print(f"   ❌ ERF {erf}: Not found")
        except Exception as e:
            print(f"   ❌ ERF {erf}: Error - {e}")

if __name__ == "__main__":
    load_erf_data_via_api()
