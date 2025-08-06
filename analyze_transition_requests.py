#!/usr/bin/env python3

import sqlite3
import os

def analyze_transition_requests():
    """Analyze existing transition requests to understand the 500 error"""
    
    db_path = os.path.join(os.path.dirname(__file__), 'altona_village_cms', 'src', 'database', 'app.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all transition requests
        cursor.execute("""
            SELECT id, status, erf_number, request_type, new_occupant_type, 
                   new_occupant_first_name, new_occupant_last_name, migration_completed
            FROM user_transition_requests
        """)
        
        requests = cursor.fetchall()
        
        print(f"Found {len(requests)} transition requests:")
        print("=" * 80)
        
        for req in requests:
            req_id, status, erf, req_type, new_occ_type, new_first, new_last, migration_completed = req
            
            print(f"\nRequest ID: {req_id}")
            print(f"Status: {status}")
            print(f"ERF: {erf}")
            print(f"Request Type: {req_type}")
            print(f"New Occupant Type: {new_occ_type}")
            print(f"New Occupant First Name: {new_first}")
            print(f"New Occupant Last Name: {new_last}")
            print(f"Migration Completed: {migration_completed}")
            
            # Analyze what path this would take when status = 'completed'
            is_termination = (
                new_occ_type == 'terminated' or
                req_type == 'exit' or
                (new_occ_type in ['', 'unknown', None] and not new_first)
            )
            
            is_privacy_compliant = (
                not new_first or 
                (new_first and new_first.strip() == '') or
                not new_last or 
                (new_last and new_last.strip() == '') or
                not new_occ_type or
                new_occ_type in ['', 'unknown', None]
            )
            
            print(f"Would be termination: {is_termination}")
            print(f"Would be privacy-compliant: {is_privacy_compliant}")
            
            if is_termination:
                print("  → Would check for pending users and handle termination")
            elif is_privacy_compliant:
                print("  → Would require linking interface completion")
            else:
                print("  → Would use legacy migration method")
                
            print("-" * 40)
            
        conn.close()
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_transition_requests()
