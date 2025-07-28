#!/usr/bin/env python3
"""
Demo script for the improved address structure
Shows how the new separated fields work for gate access and sorting
"""
import sqlite3
import os
from datetime import datetime
import uuid

def add_sample_data():
    """Add sample data to demonstrate the improved address structure"""
    print("Adding sample data to demonstrate address structure...")
    
    db_path = os.path.join(os.path.dirname(__file__), 'altona_village_cms', 'src', 'database', 'app.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Sample addresses with different formats to show parsing
        sample_addresses = [
            ("John", "Smith", "33", "Yellowwood Crescent", "33 Yellowwood Crescent", "ERF001"),
            ("Mary", "Johnson", "12", "Bluegum Avenue", "12 Bluegum Avenue", "ERF002"), 
            ("David", "Williams", "45", "Oak Street", "45 Oak Street", "ERF003"),
            ("Sarah", "Brown", "7", "Pine Road", "7 Pine Road", "ERF004"),
            ("Michael", "Davis", "128", "Cedar Lane", "128 Cedar Lane", "ERF005"),
            ("Lisa", "Wilson", "3", "Maple Drive", "3 Maple Drive", "ERF006"),
            ("Robert", "Taylor", "67", "Birch Avenue", "67 Birch Avenue", "ERF007"),
            ("Emma", "Anderson", "156", "Ash Street", "156 Ash Street", "ERF008"),
        ]
        
        # Add sample users and residents
        for i, (first_name, last_name, street_num, street_name, full_addr, erf) in enumerate(sample_addresses):
            # Create user
            user_id = str(uuid.uuid4())
            email = f"{first_name.lower()}.{last_name.lower()}@example.com"
            
            cursor.execute('''
                INSERT OR IGNORE INTO users (id, email, password_hash, role, status, created_at, updated_at)
                VALUES (?, ?, ?, 'resident', 'active', ?, ?)
            ''', (user_id, email, 'dummy_hash', datetime.now(), datetime.now()))
            
            # Create resident record
            resident_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT OR IGNORE INTO residents (
                    id, user_id, first_name, last_name, phone_number, 
                    id_number, erf_number, street_number, street_name, full_address,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                resident_id, user_id, first_name, last_name, f"021555{1000+i}",
                f"ID{9000000000+i}", erf, street_num, street_name, full_addr,
                datetime.now(), datetime.now()
            ))
            
            # Make some of them owners too
            if i % 3 == 0:  # Every 3rd person is also an owner
                owner_id = str(uuid.uuid4())
                cursor.execute('''
                    INSERT OR IGNORE INTO owners (
                        id, user_id, first_name, last_name, phone_number,
                        id_number, erf_number, street_number, street_name, full_address,
                        title_deed_number, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    owner_id, user_id, first_name, last_name, f"021555{1000+i}",
                    f"ID{9000000000+i}", erf, street_num, street_name, full_addr,
                    f"TD{2024000+i}", datetime.now(), datetime.now()
                ))
        
        conn.commit()
        print("✅ Sample data added successfully!")
        
        # Show the gate access register
        print("\n📋 GATE ACCESS REGISTER (Sorted by Street Name, then Number):")
        cursor.execute("SELECT * FROM gate_access_register")
        register_entries = cursor.fetchall()
        
        if register_entries:
            print("Last Name    | First Name | Street Name        | No. | ERF     | Phone      | Type")
            print("-" * 85)
            for entry in register_entries:
                last_name, first_name, street_name, street_number, erf, phone, email, res_type, is_owner = entry
                print(f"{last_name:<12} | {first_name:<10} | {street_name:<18} | {street_number:<3} | {erf:<7} | {phone:<10} | {res_type}")
        else:
            print("No active residents found in gate register")
        
        # Show sorting comparison
        print(f"\n🔍 SORTING COMPARISON:")
        print("OLD WAY (full address sorting):")
        cursor.execute("SELECT first_name, last_name, full_address FROM residents ORDER BY full_address")
        old_sort = cursor.fetchall()
        for name in old_sort[:5]:
            print(f"  {name[1]}, {name[0]} - {name[2]}")
        
        print("\nNEW WAY (street name + numeric sort):")
        cursor.execute("""
            SELECT first_name, last_name, street_name, street_number 
            FROM residents 
            ORDER BY street_name ASC, CAST(street_number AS INTEGER) ASC
        """)
        new_sort = cursor.fetchall()
        for name in new_sort[:5]:
            print(f"  {name[1]}, {name[0]} - {name[2]} {name[3]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding sample data: {e}")
        return False
        
    finally:
        conn.close()

def show_address_structure():
    """Show the new database structure"""
    print(f"\n{'='*60}")
    print("📊 NEW ADDRESS STRUCTURE")
    print(f"{'='*60}")
    
    db_path = os.path.join(os.path.dirname(__file__), 'altona_village_cms', 'src', 'database', 'app.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n🏠 RESIDENTS TABLE STRUCTURE:")
        cursor.execute("PRAGMA table_info(residents)")
        for col in cursor.fetchall():
            if col[1] in ['street_number', 'street_name', 'full_address']:
                print(f"  ✅ {col[1]} ({col[2]}) <- NEW for better sorting")
            else:
                print(f"     {col[1]} ({col[2]})")
        
        print("\n🏢 OWNERS TABLE STRUCTURE:")
        cursor.execute("PRAGMA table_info(owners)")
        for col in cursor.fetchall():
            if col[1].startswith('postal_') or col[1] in ['street_number', 'street_name']:
                print(f"  ✅ {col[1]} ({col[2]}) <- NEW for better organization")
            else:
                print(f"     {col[1]} ({col[2]})")
        
        print("\n🚪 GATE ACCESS VIEW:")
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='view' AND name='gate_access_register'")
        view_sql = cursor.fetchone()
        if view_sql:
            print("  ✅ Automatically sorted by street name, then number")
            print("  ✅ Ready for security guards to use")
            print("  ✅ Includes resident type and owner status")
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("🏘️  DEMONSTRATING IMPROVED ADDRESS STRUCTURE")
    print("=" * 60)
    
    show_address_structure()
    
    response = input("\nAdd sample data for demonstration? (y/n): ").lower().strip()
    if response == 'y':
        add_sample_data()
    
    print(f"\n{'🎉' * 20}")
    print("🎉 IMPROVED ADDRESS SYSTEM BENEFITS:")
    print(f"{'🎉' * 20}")
    print("✅ Street names sort alphabetically (Ash, Birch, Cedar, etc.)")
    print("✅ Street numbers sort numerically (3, 7, 12, 33, 45, etc.)")
    print("✅ Gate access register is perfectly organized for security")
    print("✅ Registration forms can use separate fields")
    print("✅ No more '33 Yellowwood' vs 'Yellowwood 33' confusion")
    print("✅ Consistent data entry and retrieval")
    print("✅ Easy Excel export with proper sorting")
    print("✅ Separate postal addresses for non-resident owners")
