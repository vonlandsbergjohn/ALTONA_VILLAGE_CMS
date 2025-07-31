#!/usr/bin/env python3
"""
Fix the transition_vehicles.color column issue that's causing 500 errors
"""

import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'altona_village_cms', 'src', 'database', 'app.db')

def fix_vehicle_color_column():
    """Add the missing color column to transition_vehicles table"""
    print("🔧 Fixing transition_vehicles.color column issue...")
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if color column exists
        cursor.execute('PRAGMA table_info(transition_vehicles)')
        columns = [row[1] for row in cursor.fetchall()]
        
        print(f"Current transition_vehicles columns: {columns}")
        
        if 'color' not in columns:
            print("❌ 'color' column missing, adding it...")
            cursor.execute('ALTER TABLE transition_vehicles ADD COLUMN color VARCHAR(50)')
            conn.commit()
            print("✅ Added 'color' column to transition_vehicles")
        else:
            print("✅ 'color' column already exists")
        
        # Also check if vehicle_color exists (duplicate?)
        if 'vehicle_color' in columns and 'color' in columns:
            print("⚠️  Both 'vehicle_color' and 'color' columns exist")
            # Copy data from vehicle_color to color if color is empty
            cursor.execute('''
                UPDATE transition_vehicles 
                SET color = vehicle_color 
                WHERE color IS NULL AND vehicle_color IS NOT NULL
            ''')
            conn.commit()
            print("✅ Copied data from vehicle_color to color column")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error fixing color column: {e}")
        return False

def test_vehicle_query():
    """Test the vehicle query that was failing"""
    print("\n🧪 Testing the failing vehicle query...")
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # This is the query that was failing according to the logs
        cursor.execute('''
            SELECT 
                id, transition_request_id, vehicle_make, vehicle_model, 
                license_plate, color, created_at
            FROM transition_vehicles 
            LIMIT 1
        ''')
        
        result = cursor.fetchone()
        if result:
            print("✅ Vehicle query now works!")
            print(f"Sample result: {result}")
        else:
            print("✅ Vehicle query works (no data found)")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Vehicle query still failing: {e}")
        return False

def main():
    print("🔧 Fixing Transition Request Management Issues")
    print("=" * 50)
    
    # Fix the color column issue
    fix_success = fix_vehicle_color_column()
    
    if fix_success:
        # Test the query
        test_success = test_vehicle_query()
        
        if test_success:
            print("\n🎉 FIXES APPLIED SUCCESSFULLY!")
            print("✅ The manage request page should now load properly")
            print("✅ Admin can now view individual transition request details")
        else:
            print("\n❌ Query test failed - there may be other issues")
    else:
        print("\n❌ Failed to apply fixes")
    
    return fix_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
