#!/usr/bin/env python3
"""
Database migration script for improved address and name structure
Separates street numbers, street names, and improves sorting capabilities
"""
import sqlite3
import os
import uuid
from datetime import datetime

def migrate_address_structure():
    """Migrate database to separate address components for better sorting"""
    print("Starting address structure migration...")
    
    # Connect to database
    db_path = os.path.join(os.path.dirname(__file__), 'altona_village_cms', 'src', 'database', 'app.db')
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Update residents table structure
        print("1. Updating residents table structure...")
        
        # Create new residents table with improved structure
        cursor.execute('''
            CREATE TABLE residents_new (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL UNIQUE,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                phone_number VARCHAR(20),
                emergency_contact_name VARCHAR(255),
                emergency_contact_number VARCHAR(20),
                id_number VARCHAR(50) NOT NULL,
                erf_number VARCHAR(50) NOT NULL,
                -- Separated address components for better sorting
                street_number VARCHAR(10) NOT NULL,
                street_name VARCHAR(100) NOT NULL,
                -- Full address still available for display
                full_address VARCHAR(255) NOT NULL,
                moving_in_date DATE,
                moving_out_date DATE,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Migrate existing residents data with address parsing
        cursor.execute('SELECT * FROM residents')
        existing_residents = cursor.fetchall()
        
        for resident in existing_residents:
            # Try to parse address into components
            address = resident[9]  # address column
            street_number, street_name = parse_address(address)
            
            cursor.execute('''
                INSERT INTO residents_new (
                    id, user_id, first_name, last_name, phone_number,
                    emergency_contact_name, emergency_contact_number, id_number,
                    erf_number, street_number, street_name, full_address,
                    moving_in_date, moving_out_date, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                resident[0], resident[1], resident[2], resident[3], resident[4],
                resident[5], resident[6], resident[7], resident[8],
                street_number, street_name, address,
                resident[10], resident[11], resident[12], resident[13]
            ))
        
        # Drop old table and rename new one
        cursor.execute('DROP TABLE residents')
        cursor.execute('ALTER TABLE residents_new RENAME TO residents')
        
        # Recreate indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_residents_user_id ON residents(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_residents_street_name ON residents(street_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_residents_last_name ON residents(last_name)')
        
        print("✅ Residents table updated with separated address components")
        
        # 2. Update owners table structure
        print("2. Updating owners table structure...")
        
        cursor.execute('''
            CREATE TABLE owners_new (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL UNIQUE,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                phone_number VARCHAR(20),
                id_number VARCHAR(50) NOT NULL,
                erf_number VARCHAR(50) NOT NULL,
                -- Separated address components for better sorting
                street_number VARCHAR(10) NOT NULL,
                street_name VARCHAR(100) NOT NULL,
                -- Full address still available for display
                full_address VARCHAR(255) NOT NULL,
                -- Owner-specific fields
                title_deed_number VARCHAR(100),
                acquisition_date DATE,
                -- Separate postal address components
                postal_street_number VARCHAR(10),
                postal_street_name VARCHAR(100),
                postal_suburb VARCHAR(100),
                postal_city VARCHAR(100),
                postal_code VARCHAR(10),
                postal_province VARCHAR(50),
                full_postal_address VARCHAR(500),
                emergency_contact_name VARCHAR(255),
                emergency_contact_number VARCHAR(20),
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Migrate existing owners data
        cursor.execute('SELECT * FROM owners')
        existing_owners = cursor.fetchall()
        
        for owner in existing_owners:
            # Try to parse address into components
            address = owner[7]  # address column
            street_number, street_name = parse_address(address)
            
            cursor.execute('''
                INSERT INTO owners_new (
                    id, user_id, first_name, last_name, phone_number,
                    id_number, erf_number, street_number, street_name, full_address,
                    title_deed_number, acquisition_date, 
                    postal_street_number, postal_street_name, postal_suburb,
                    postal_city, postal_code, postal_province, full_postal_address,
                    emergency_contact_name, emergency_contact_number,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                owner[0], owner[1], owner[2], owner[3], owner[4],
                owner[5], owner[6], street_number, street_name, address,
                owner[8], owner[9],  # title_deed_number, acquisition_date
                None, None, None, None, None, None, owner[10],  # postal components
                owner[11], owner[12],  # emergency contacts
                owner[13], owner[14]  # timestamps
            ))
        
        # Drop old table and rename new one
        cursor.execute('DROP TABLE owners')
        cursor.execute('ALTER TABLE owners_new RENAME TO owners')
        
        # Recreate indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_owners_user_id ON owners(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_owners_street_name ON owners(street_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_owners_last_name ON owners(last_name)')
        
        print("✅ Owners table updated with separated address components")
        
        # 3. Update properties table to include separated address
        print("3. Updating properties table...")
        
        try:
            cursor.execute('ALTER TABLE properties ADD COLUMN street_number VARCHAR(10)')
            cursor.execute('ALTER TABLE properties ADD COLUMN street_name VARCHAR(100)')
            print("✅ Properties table updated with address components")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("✅ Properties table already has address components")
            else:
                print(f"⚠️  Warning: {e}")
        
        # Update existing properties with parsed addresses
        cursor.execute('SELECT id, address FROM properties WHERE street_number IS NULL')
        properties = cursor.fetchall()
        for prop in properties:
            street_number, street_name = parse_address(prop[1])
            cursor.execute('''
                UPDATE properties 
                SET street_number = ?, street_name = ?
                WHERE id = ?
            ''', (street_number, street_name, prop[0]))
        
        # 4. Create gate access view for security
        print("4. Creating gate access view...")
        cursor.execute('DROP VIEW IF EXISTS gate_access_register')
        cursor.execute('''
            CREATE VIEW gate_access_register AS
            SELECT 
                r.last_name,
                r.first_name,
                r.street_name,
                r.street_number,
                r.erf_number,
                r.phone_number,
                u.email,
                'Resident' as resident_type,
                CASE WHEN o.id IS NOT NULL THEN 'Yes' ELSE 'No' END as is_owner
            FROM residents r
            JOIN users u ON r.user_id = u.id
            LEFT JOIN owners o ON r.user_id = o.user_id
            WHERE u.status = 'active'
            ORDER BY r.street_name ASC, CAST(r.street_number AS INTEGER) ASC, r.last_name ASC
        ''')
        print("✅ Gate access view created")
        
        # Commit changes
        conn.commit()
        print("✅ Address structure migration completed successfully!")
        
        # Verify migration
        cursor.execute('SELECT COUNT(*) FROM residents')
        residents_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM owners')
        owners_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT * FROM gate_access_register LIMIT 5')
        gate_sample = cursor.fetchall()
        
        print(f"\n📊 Migration Results:")
        print(f"   - Residents: {residents_count}")
        print(f"   - Owners: {owners_count}")
        print(f"   - Gate access view: {len(gate_sample)} sample entries")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def parse_address(address):
    """Parse address to extract street number and street name"""
    if not address:
        return "", ""
    
    # Remove common suffixes that shouldn't be in the basic address
    address = address.replace("Altona Village", "").replace("Worcester", "").strip()
    
    # Try to find number at the beginning
    parts = address.split()
    street_number = ""
    street_name = ""
    
    if parts:
        # Check if first part is a number
        if parts[0].isdigit():
            street_number = parts[0]
            street_name = " ".join(parts[1:]).strip()
        else:
            # Check if last part is a number
            if parts[-1].isdigit():
                street_number = parts[-1]
                street_name = " ".join(parts[:-1]).strip()
            else:
                # Look for number in middle or extract first number found
                for i, part in enumerate(parts):
                    if part.isdigit():
                        street_number = part
                        street_name = " ".join(parts[:i] + parts[i+1:]).strip()
                        break
                
                # If no number found, use entire address as street name
                if not street_number:
                    street_name = address
    
    return street_number or "", street_name or address

if __name__ == "__main__":
    success = migrate_address_structure()
    if success:
        print("\n🎉 Address structure migration completed!")
        print("Benefits:")
        print("  • Street names can be sorted alphabetically")
        print("  • Street numbers are separate for proper numeric sorting")
        print("  • Gate access register is properly organized")
        print("  • Registration forms can use separate fields")
        print("  • Better data consistency and filtering")
    else:
        print("\n💥 Migration failed. Please check the errors above.")
