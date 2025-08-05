#!/usr/bin/env python3
"""
Simple check - just login and check gate register
"""

import requests
import time

def simple_check():
    print("Testing gate register fix...")
    
    # Wait for server
    time.sleep(3)
    
    try:
        # Login
        response = requests.post("http://localhost:5000/api/auth/login", 
                               json={"email": "vonlandsbergjohn@gmail.com", "password": "dGdFHLCJxx44ykq"},
                               timeout=10)
        
        if response.status_code == 200:
            token = response.json()['access_token']
            print("✅ Login successful")
            
            # Check gate register
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get("http://localhost:5000/api/admin/gate-register-legacy", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                entries = data.get('data', [])
                print(f"✅ Gate register entries: {len(entries)}")
                
                for entry in entries:
                    print(f"   • {entry.get('first_name')} {entry.get('surname')} - {entry.get('resident_status')}")
                
                return len(entries)
            else:
                print(f"❌ Gate register error: {response.status_code}")
        else:
            print(f"❌ Login failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return 0

if __name__ == "__main__":
    simple_check()
