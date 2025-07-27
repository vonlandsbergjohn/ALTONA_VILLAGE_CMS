#!/usr/bin/env python3
"""
Database migration script for Multi-Group System
Adds Owner table and migrates existing data
"""
import sqlite3
import os
import uuid
from datetime import datetime

def migrate_multi_group_system():
    """Migrate database to support multi-group system"""
    print("Starting multi-group system migration...")
    
    # Connect to database
    db_path = os.path.join(os.path.dirname(__file__), 'altona_village_cms', 'src', 'database', 'app.db')
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Create the owners table
        print("1. Creating owners table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS owners (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL UNIQUE,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                phone_number VARCHAR(20),
                id_number VARCHAR(50) NOT NULL,
                erf_number VARCHAR(50) NOT NULL,
                address VARCHAR(255) NOT NULL,
                title_deed_number VARCHAR(100),
                acquisition_date DATE,
                postal_address VARCHAR(255),
                emergency_contact_name VARCHAR(255),
                emergency_contact_number VARCHAR(20),
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        print("✅ Owners table created")
        
        # 2. Add owner_id column to properties table
        print("2. Adding owner_id to properties table...")
        try:
            cursor.execute('ALTER TABLE properties ADD COLUMN owner_id VARCHAR(36)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_properties_owner_id ON properties(owner_id)')
            print("✅ owner_id column added to properties")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("✅ owner_id column already exists in properties")
            else:
                raise e
        
        # 3. Migrate existing residents who are owners to owners table
        print("3. Migrating existing owner-residents...")
        cursor.execute('''
            SELECT r.id, r.user_id, r.first_name, r.last_name, r.phone_number, 
                   r.id_number, r.erf_number, r.address, r.emergency_contact_name, 
                   r.emergency_contact_number, r.created_at, r.updated_at
            FROM residents r
            WHERE r.is_owner = 1
        ''')
        owner_residents = cursor.fetchall()
        
        migrated_count = 0
        for resident in owner_residents:
            # Check if owner record already exists
            cursor.execute('SELECT id FROM owners WHERE user_id = ?', (resident[1],))
            if cursor.fetchone():
                print(f"   Owner record already exists for user {resident[1]}")
                continue
            
            # Create owner record
            owner_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO owners (
                    id, user_id, first_name, last_name, phone_number, id_number, 
                    erf_number, address, emergency_contact_name, emergency_contact_number,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                owner_id, resident[1], resident[2], resident[3], resident[4],
                resident[5], resident[6], resident[7], resident[8], resident[9],
                resident[10], resident[11]
            ))
            migrated_count += 1
        
        print(f"✅ Migrated {migrated_count} owner-residents to owners table")
        
        # 4. Remove is_owner column from residents table
        print("4. Removing is_owner column from residents table...")
        try:
            # SQLite doesn't support DROP COLUMN, so we need to recreate the table
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
                    address VARCHAR(255) NOT NULL,
                    moving_in_date DATE,
                    moving_out_date DATE,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Copy data without is_owner column
            cursor.execute('''
                INSERT INTO residents_new 
                SELECT id, user_id, first_name, last_name, phone_number, 
                       emergency_contact_name, emergency_contact_number, id_number, 
                       erf_number, address, moving_in_date, moving_out_date, 
                       created_at, updated_at
                FROM residents
            ''')
            
            # Drop old table and rename new one
            cursor.execute('DROP TABLE residents')
            cursor.execute('ALTER TABLE residents_new RENAME TO residents')
            
            # Recreate indexes and foreign keys
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_residents_user_id ON residents(user_id)')
            
            print("✅ Removed is_owner column from residents table")
        except Exception as e:
            print(f"⚠️  Warning: Could not remove is_owner column: {e}")
            print("   This doesn't affect functionality, column will be ignored")
        
        # 5. Update property relationships
        print("5. Updating property-owner relationships...")
        cursor.execute('''
            UPDATE properties 
            SET owner_id = (
                SELECT o.id FROM owners o 
                WHERE o.erf_number = properties.erf_number
                LIMIT 1
            )
            WHERE owner_id IS NULL
        ''')
        
        updated_properties = cursor.rowcount
        print(f"✅ Updated {updated_properties} property-owner relationships")
        
        # 6. Verify migration
        print("6. Verifying migration...")
        cursor.execute('SELECT COUNT(*) FROM owners')
        owners_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM residents')
        residents_count = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM users u 
            JOIN residents r ON u.id = r.user_id 
            JOIN owners o ON u.id = o.user_id
        ''')
        owner_residents_count = cursor.fetchone()[0]
        
        print(f"✅ Migration verification:")
        print(f"   - Total owners: {owners_count}")
        print(f"   - Total residents: {residents_count}")
        print(f"   - Owner-residents: {owner_residents_count}")
        
        # Commit changes
        conn.commit()
        print("✅ Migration completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = migrate_multi_group_system()
    if success:
        print("\n🎉 Multi-group system is now ready!")
        print("Your system now supports:")
        print("  • Residents (including owner-residents)")
        print("  • Owners (including non-resident owners)")
        print("  • Separate bulk communication to each group")
    else:
        print("\n💥 Migration failed. Please check the errors above.")
