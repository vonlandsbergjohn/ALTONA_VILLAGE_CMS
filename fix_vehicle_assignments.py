#!/usr/bin/env python3
"""
Fix Vehicle Assignment Issue
The vehicles are not linked to the correct user records
"""

import psycopg2
import os

DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://postgres:%23Johnvonl1977@localhost:5432/altona_village_db")

def fix_vehicle_assignments():
    """Fix vehicle assignments to the correct user"""
    
    print("🔧 FIXING VEHICLE ASSIGNMENTS")
    print("=" * 60)
    
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Get the current user details
        target_email = "hi@hi1"
        cursor.execute("SELECT id, email, role FROM users WHERE email = %s", (target_email,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ User {target_email} not found")
            return
        
        user_id = user[0]
        print(f"Target User: {target_email} (ID: {user_id})")
        
        # Get user's resident and owner records
        cursor.execute("SELECT id FROM residents WHERE user_id = %s", (user_id,))
        resident = cursor.fetchone()
        resident_id = resident[0] if resident else None
        
        cursor.execute("SELECT id FROM owners WHERE user_id = %s", (user_id,))
        owner = cursor.fetchone()
        owner_id = owner[0] if owner else None
        
        print(f"Resident ID: {resident_id}")
        print(f"Owner ID: {owner_id}")
        
        # Get all vehicles that might need reassignment
        cursor.execute("SELECT id, registration_number, owner_id, resident_id FROM vehicles")
        all_vehicles = cursor.fetchall()
        
        print(f"\nFound {len(all_vehicles)} total vehicles")
        
        # Let's assign all recent vehicles to this user (since they appear to be test vehicles)
        recent_vehicles = []
        for vehicle in all_vehicles:
            vehicle_id, reg_number, current_owner_id, current_resident_id = vehicle
            # These look like test registrations that should belong to our test user
            if reg_number in ['CW55599', 'TEST123', 'NEW999GP', 'AUTH001', 'AUTH002', 'AUTH003', 'CW52525']:
                recent_vehicles.append(vehicle)
        
        if recent_vehicles:
            print(f"\n🎯 ASSIGNING VEHICLES TO USER {target_email}:")
            
            for vehicle in recent_vehicles:
                vehicle_id, reg_number, current_owner_id, current_resident_id = vehicle
                print(f"   - {reg_number}")
                
                # Update the vehicle to link to the correct user
                # If user is both resident and owner, link to resident for vehicle access
                if resident_id:
                    cursor.execute("""
                        UPDATE vehicles SET resident_id = %s, owner_id = %s WHERE id = %s
                    """, (resident_id, owner_id, vehicle_id))
                elif owner_id:
                    cursor.execute("""
                        UPDATE vehicles SET owner_id = %s, resident_id = NULL WHERE id = %s
                    """, (owner_id, vehicle_id))
            
            conn.commit()
            print(f"✅ Updated {len(recent_vehicles)} vehicles")
            
            # Verify the changes
            print(f"\n📋 VERIFICATION:")
            cursor.execute("""
                SELECT registration_number, resident_id, owner_id 
                FROM vehicles 
                WHERE resident_id = %s OR owner_id = %s
            """, (resident_id, owner_id))
            
            user_vehicles = cursor.fetchall()
            print(f"User now has {len(user_vehicles)} vehicles:")
            for vehicle in user_vehicles:
                print(f"   - {vehicle[0]} (Resident: {vehicle[1]}, Owner: {vehicle[2]})")
                
        else:
            print("No vehicles to reassign")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_vehicle_assignments()
