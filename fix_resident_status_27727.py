#!/usr/bin/env python3
"""
Fix Gate Register Issue: Update resident status from 'approved' to 'active'
The transition system creates residents with 'active' status, but somehow 
Marilize's record shows 'approved'. Let's fix this directly.
"""

import requests
import json

def fix_resident_status():
    """Fix the resident status issue"""
    
    print("🔧 FIXING RESIDENT STATUS FOR GATE REGISTER")
    print("=" * 60)
    
    # Login as admin first
    login_url = "http://localhost:5000/api/auth/login"
    login_data = {
        "email": "vonlandsbergjohn@gmail.com",
        "password": "dGdFHLCJxx44ykq"
    }
    
    try:
        # Login
        print("1. Logging in as admin...")
        response = requests.post(login_url, json=login_data)
        if response.status_code == 200:
            token = response.json()['access_token']
            print("   ✅ Login successful")
        else:
            print(f"   ❌ Login failed: {response.status_code} - {response.text}")
            return
        
        # Get residents to identify Marilize
        print("\n2. Fetching residents...")
        residents_url = "http://localhost:5000/api/admin/residents"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(residents_url, headers=headers)
        if response.status_code == 200:
            residents = response.json()
            print(f"   ✅ Found {len(residents)} residents")
            
            # Find Marilize (ERF 27727, approved status)
            marilize = None
            for resident in residents:
                if (resident.get('erf_number') == '27727' and 
                    resident.get('status') == 'approved' and
                    'Marilize' in resident.get('first_name', '')):
                    marilize = resident
                    break
            
            if marilize:
                print(f"   🎯 Found Marilize: {marilize.get('first_name')} {marilize.get('last_name')}")
                print(f"      Current Status: {marilize.get('status')}")
                print(f"      Resident ID: {marilize.get('id')}")
                
                # Update status to 'active'
                print("\n3. Updating status to 'active'...")
                update_url = f"http://localhost:5000/api/admin/residents/{marilize.get('id')}"
                update_data = {
                    "status": "active"
                }
                
                response = requests.put(update_url, json=update_data, headers=headers)
                if response.status_code == 200:
                    print("   ✅ Status updated successfully!")
                    
                    # Test gate register again
                    print("\n4. Testing gate register...")
                    gate_register_url = "http://localhost:5000/api/admin/gate-register-legacy"
                    response = requests.get(gate_register_url, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        print(f"   ✅ Gate register now has {data.get('total_entries', 0)} entries")
                        
                        # Look for ERF 27727 entries
                        erf_27727_entries = []
                        for entry in data.get('data', []):
                            if entry.get('erf_number') == '27727':
                                erf_27727_entries.append(entry)
                        
                        print(f"   🎯 ERF 27727 entries found: {len(erf_27727_entries)}")
                        for entry in erf_27727_entries:
                            print(f"      ✅ {entry.get('first_name')} {entry.get('surname')} - {entry.get('resident_status')}")
                    else:
                        print(f"   ❌ Gate register error: {response.status_code}")
                else:
                    print(f"   ❌ Update failed: {response.status_code} - {response.text}")
            else:
                print("   ❌ Could not find Marilize's resident record")
                print("   Available residents:")
                for resident in residents:
                    print(f"      - {resident.get('first_name')} {resident.get('last_name')} (ERF {resident.get('erf_number')}, Status: {resident.get('status')})")
        else:
            print(f"   ❌ Failed to fetch residents: {response.status_code}")
        
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Backend server not running on localhost:5000")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    fix_resident_status()
