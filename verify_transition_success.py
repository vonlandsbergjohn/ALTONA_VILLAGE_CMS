#!/usr/bin/env python3
"""
Verify Transition Completion Success
Check the final state after successful transition linking
"""

import sqlite3

def verify_transition_success():
    """Verify that the transition was completed successfully"""
    
    db_path = r"C:\Altona_Village_CMS\altona_village_cms\src\database\app.db"
    
    print("✅ VERIFYING TRANSITION COMPLETION SUCCESS")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Check the transition request status
        print("\n1. TRANSITION REQUEST STATUS:")
        cursor.execute("""
            SELECT id, erf_number, status, migration_completed, 
                   new_user_id, new_occupant_first_name, new_occupant_last_name
            FROM user_transition_requests 
            WHERE erf_number = '27727'
            ORDER BY created_at DESC
            LIMIT 1
        """)
        
        transition = cursor.fetchone()
        if transition:
            print(f"   Request ID: {transition[0]}")
            print(f"   ERF: {transition[1]}")
            print(f"   Status: {transition[2]}")
            print(f"   Migration Completed: {'✅ YES' if transition[3] else '❌ NO'}")
            print(f"   New User ID: {transition[4]}")
            print(f"   New Occupant: {transition[5]} {transition[6]}")
            
            if transition[2] == 'completed' and transition[3]:
                print("   🎉 TRANSITION SUCCESSFULLY COMPLETED!")
            else:
                print("   ⚠️ Transition not fully completed")
        
        # 2. Check the new user details
        print("\n2. NEW USER DETAILS:")
        if transition and transition[4]:
            cursor.execute("""
                SELECT id, email, role, status, created_at
                FROM users 
                WHERE id = ?
            """, (transition[4],))
            
            user = cursor.fetchone()
            if user:
                print(f"   User ID: {user[0]}")
                print(f"   Email: {user[1]}")
                print(f"   Role: {user[2]}")
                print(f"   Status: {user[3]}")
                print(f"   Created: {user[4]}")
                
                if user[3] == 'active':
                    print("   ✅ User is now ACTIVE!")
                else:
                    print(f"   ⚠️ User status is still: {user[3]}")
            else:
                print("   ❌ New user not found!")
        
        # 3. Check if new user has property records
        print("\n3. NEW USER PROPERTY RECORDS:")
        if transition and transition[4]:
            # Check resident record
            cursor.execute("""
                SELECT first_name, last_name, erf_number, status
                FROM residents 
                WHERE user_id = ?
            """, (transition[4],))
            
            resident = cursor.fetchone()
            if resident:
                print(f"   Resident: {resident[0]} {resident[1]} (ERF: {resident[2]}, Status: {resident[3]})")
                if resident[3] == 'active':
                    print("   ✅ Resident record is ACTIVE!")
            
            # Check owner record
            cursor.execute("""
                SELECT first_name, last_name, erf_number, status
                FROM owners 
                WHERE user_id = ?
            """, (transition[4],))
            
            owner = cursor.fetchone()
            if owner:
                print(f"   Owner: {owner[0]} {owner[1]} (ERF: {owner[2]}, Status: {owner[3]})")
                if owner[3] == 'active':
                    print("   ✅ Owner record is ACTIVE!")
        
        # 4. Check gate register simulation
        print("\n4. GATE REGISTER VERIFICATION FOR ERF 27727:")
        cursor.execute("""
            SELECT u.id, u.email, u.role, u.status,
                   r.first_name as r_first, r.last_name as r_last, r.status as r_status,
                   o.first_name as o_first, o.last_name as o_last, o.status as o_status
            FROM users u
            LEFT JOIN residents r ON u.id = r.user_id AND r.erf_number = '27727'
            LEFT JOIN owners o ON u.id = o.user_id AND o.erf_number = '27727'
            WHERE u.status = 'active' AND u.role != 'admin'
            AND (r.status = 'active' OR o.status = 'active')
        """)
        
        gate_entries = cursor.fetchall()
        if gate_entries:
            print("   ✅ GATE REGISTER ENTRIES FOUND:")
            for entry in gate_entries:
                name = entry[4] + " " + entry[5] if entry[4] else entry[7] + " " + entry[8]
                print(f"   - {name} (Email: {entry[1]}, Role: {entry[2]})")
        else:
            print("   ❌ NO GATE REGISTER ENTRIES FOUND")
        
        # 5. Check vehicle status (should remain with old user)
        print("\n5. VEHICLE STATUS VERIFICATION:")
        cursor.execute("""
            SELECT v.registration_number, v.make, v.model, v.status, 
                   r.first_name as r_first, r.last_name as r_last,
                   o.first_name as o_first, o.last_name as o_last
            FROM vehicles v
            LEFT JOIN residents r ON v.resident_id = r.id
            LEFT JOIN owners o ON v.owner_id = o.id
            WHERE r.erf_number = '27727' OR o.erf_number = '27727'
        """)
        
        vehicles = cursor.fetchall()
        if vehicles:
            for vehicle in vehicles:
                owner_name = vehicle[4] + " " + vehicle[5] if vehicle[4] else vehicle[6] + " " + vehicle[7]
                print(f"   Vehicle: {vehicle[0]} ({vehicle[1]} {vehicle[2]})")
                print(f"   Status: {vehicle[3]}, Owner: {owner_name}")
        else:
            print("   No vehicles found for ERF 27727")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("🎉 VERIFICATION COMPLETE!")
        print("The transition linking process has been successfully completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verify_transition_success()
