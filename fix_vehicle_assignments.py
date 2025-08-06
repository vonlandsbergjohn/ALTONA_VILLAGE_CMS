#!/usr/bin/env python3
"""
Fix Vehicle Assignment Issue
The vehicles are not linked to the correct user records
"""

import sqlite3
import os

def fix_vehicle_assignments():
    """Fix vehicle assignments to the correct user"""
    
    db_path = os.path.join('altona_village_cms', 'src', 'database', 'app.db')
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔧 FIXING VEHICLE ASSIGNMENTS")
    print("=" * 60)
    
    # Get the current user details
    target_email = "hi@hi1"
    cursor.execute("SELECT id, email, role FROM users WHERE email = ?", (target_email,))
    user = cursor.fetchone()
    
    if not user:
        print(f"❌ User {target_email} not found")
        return
    
    user_id = user[0]
    print(f"Target User: {target_email} (ID: {user_id})")
    
    # Get user's resident and owner records
    cursor.execute("SELECT id FROM residents WHERE user_id = ?", (user_id,))
    resident = cursor.fetchone()
    resident_id = resident[0] if resident else None
    
    cursor.execute("SELECT id FROM owners WHERE user_id = ?", (user_id,))
    owner = cursor.fetchone()
    owner_id = owner[0] if owner else None
    
    print(f"Resident ID: {resident_id}")
    print(f"Owner ID: {owner_id}")
    
    # Get all vehicles that might need reassignment
    cursor.execute("SELECT id, registration_number, owner_id, resident_id FROM vehicles")
    all_vehicles = cursor.fetchall()
    
    print(f"\nFound {len(all_vehicles)} total vehicles")
    
    # Since the user used the interface to register vehicles, we should assign them to the user
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
                    UPDATE vehicles 
                    SET resident_id = ?, owner_id = ?
                    WHERE id = ?
                """, (resident_id, owner_id, vehicle_id))
            elif owner_id:
                cursor.execute("""
                    UPDATE vehicles 
                    SET owner_id = ?, resident_id = NULL
                    WHERE id = ?
                """, (owner_id, vehicle_id))
        
        conn.commit()
        print(f"✅ Updated {len(recent_vehicles)} vehicles")
        
        # Verify the changes
        print(f"\n📋 VERIFICATION:")
        cursor.execute("""
            SELECT registration_number, resident_id, owner_id 
            FROM vehicles 
            WHERE resident_id = ? OR owner_id = ?
        """, (resident_id, owner_id))
        
        user_vehicles = cursor.fetchall()
        print(f"User now has {len(user_vehicles)} vehicles:")
        for vehicle in user_vehicles:
            print(f"   - {vehicle[0]} (Resident: {vehicle[1]}, Owner: {vehicle[2]})")
            
    else:
        print("No vehicles to reassign")
    
    conn.close()

if __name__ == "__main__":
    fix_vehicle_assignments()
