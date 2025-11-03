#!/usr/bin/env python3
"""
Quick Debug for Transition Status Issues
Check the current state and identify why status updates are failing
"""

import sys
import os
import psycopg2

DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://postgres:%23Johnvonl1977@localhost:5432/altona_village_db")

def debug_transition_status():
    """Check the current transition status and identify issues"""
    
    print("🔍 DEBUGGING TRANSITION STATUS ISSUES")
    print("=" * 60)
    
    with psycopg2.connect(DATABASE_URL) as conn:
        cursor = conn.cursor()
        
        # 1. Check current transition requests
        print("\n1. CURRENT TRANSITION REQUESTS:")
        cursor.execute("""
            SELECT id, erf_number, status, migration_completed, 
                   new_user_id, new_occupant_first_name, new_occupant_last_name,
                   created_at, updated_at
            FROM user_transition_requests 
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        requests = cursor.fetchall()
        if requests:
            for req in requests:
                print(f"   ID: {req[0]}, ERF: {req[1]}, Status: {req[2]}")
                print(f"   Migration Completed: {req[3]}, New User ID: {req[4]}")
                print(f"   New Occupant: {req[5]} {req[6]}")
                print(f"   Created: {req[7]}, Updated: {req[8]}")
                print("   ---")
        else:
            print("   No transition requests found")
        
        # 2. Check users created in the last hour
        print("\n2. RECENTLY CREATED USERS:")
        cursor.execute("""
            SELECT id, email, role, status, created_at
            FROM users 
            WHERE created_at > NOW() - INTERVAL '1 hour'
            ORDER BY created_at DESC
        """)
        
        users = cursor.fetchall()
        if users:
            for user in users:
                print(f"   ID: {user[0]}, Email: {user[1]}, Role: {user[2]}, Status: {user[3]}")
                print(f"   Created: {user[4]}")
        else:
            print("   No recently created users")
        
        # 3. Check for any pending migrations
        print("\n3. PENDING MIGRATIONS (migration_completed = 0):")
        cursor.execute("""
            SELECT id, erf_number, status, new_user_id
            FROM user_transition_requests 
            WHERE migration_completed = 0 OR migration_completed IS NULL
            ORDER BY created_at DESC
        """)
        
        pending = cursor.fetchall()
        if pending:
            for req in pending:
                print(f"   Request ID: {req[0]}, ERF: {req[1]}, Status: {req[2]}, New User ID: {req[3]}")
        else:
            print("   No pending migrations found")
        
        # 4. Check if there are users with 'approved' status (new status)
        print("\n4. USERS WITH 'APPROVED' STATUS:")
        cursor.execute("""
            SELECT id, email, role, status
            FROM users 
            WHERE status = 'approved'
        """)
        
        approved_users = cursor.fetchall()
        if approved_users:
            for user in approved_users:
                print(f"   ID: {user[0]}, Email: {user[1]}, Role: {user[2]}, Status: {user[3]}")
        else:
            print("   No users with 'approved' status")
        
        # 5. Check the latest transition for ERF 27727 specifically
        print("\n5. LATEST TRANSITION FOR ERF 27727:")
        cursor.execute("""
            SELECT id, status, migration_completed, new_user_id, 
                   new_occupant_first_name, new_occupant_last_name,
                   new_occupant_type, created_at
            FROM user_transition_requests 
            WHERE erf_number = '27727'
            ORDER BY created_at DESC
            LIMIT 1
        """)
        
        erf_27727 = cursor.fetchone()
        if erf_27727:
            print(f"   Request ID: {erf_27727[0]}")
            print(f"   Status: {erf_27727[1]}")
            print(f"   Migration Completed: {erf_27727[2]}")
            print(f"   New User ID: {erf_27727[3]}")
            print(f"   New Occupant: {erf_27727[4]} {erf_27727[5]} ({erf_27727[6]})") # type: ignore
            print(f"   Created At: {erf_27727[7]}")
            
            # If there's a new user, check their details
            if erf_27727[3]:
                cursor.execute("""
                    SELECT email, role, status
                    FROM users 
                    WHERE id = %s
                """, (str(erf_27727[3]),))
                
                user_details = cursor.fetchone()
                if user_details:
                    print(f"   New User Details: {user_details[0]} (Role: {user_details[1]}, Status: {user_details[2]})")
                else:
                    print(f"   ❌ New User ID {erf_27727[3]} NOT FOUND!")
        else:
            print("   No transition request found for ERF 27727")
        
    print("\n" + "=" * 60)
    print("✅ Debug complete. Check the output above for issues.")

if __name__ == "__main__":
    debug_transition_status()
