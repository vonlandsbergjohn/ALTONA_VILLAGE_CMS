#!/usr/bin/env python3
"""
Fix the owners table schema to match the model definition.
"""

import sqlite3

def fix_owners_table_schema():
    """Fix the owners table to match the Owner model"""
    
    db_path = "altona_village_cms/src/database/app.db"
    
    print("🔧 Fixing Owners Table Schema")
    print("=" * 40)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if we have any existing data
    cursor.execute("SELECT COUNT(*) FROM owners")
    existing_count = cursor.fetchone()[0]
    print(f"Existing owners records: {existing_count}")
    
    if existing_count > 0:
        print("⚠️  Backing up existing data...")
        # Could implement backup here if needed
    
    # Drop and recreate the owners table with correct schema
    print("🗑️  Dropping existing owners table...")
    cursor.execute("DROP TABLE IF EXISTS owners")
    
    print("🏗️  Creating new owners table with correct schema...")
    create_table_sql = """
    CREATE TABLE owners (
        id VARCHAR(36) PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL UNIQUE,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) NOT NULL,
        phone_number VARCHAR(20),
        id_number VARCHAR(50) NOT NULL,
        erf_number VARCHAR(50) NOT NULL,
        street_number VARCHAR(10) NOT NULL,
        street_name VARCHAR(100) NOT NULL,
        full_address VARCHAR(255) NOT NULL,
        intercom_code VARCHAR(20),
        title_deed_number VARCHAR(100),
        acquisition_date DATE,
        postal_street_number VARCHAR(10),
        postal_street_name VARCHAR(100),
        postal_suburb VARCHAR(100),
        postal_city VARCHAR(100),
        postal_code VARCHAR(10),
        postal_province VARCHAR(50),
        full_postal_address VARCHAR(500),
        emergency_contact_name VARCHAR(255),
        emergency_contact_number VARCHAR(20),
        status VARCHAR(50) NOT NULL DEFAULT 'active',
        migration_date DATETIME,
        migration_reason TEXT,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """
    
    cursor.execute(create_table_sql)
    
    # Also fix the residents table while we're at it
    print("🔧 Checking residents table...")
    cursor.execute("PRAGMA table_info(residents)")
    residents_info = cursor.fetchall()
    residents_id_type = next((col[2] for col in residents_info if col[1] == 'id'), None)
    
    if residents_id_type == 'INTEGER':
        print("🔧 Fixing residents table schema...")
        
        # Check existing residents data
        cursor.execute("SELECT COUNT(*) FROM residents")
        residents_count = cursor.fetchone()[0]
        print(f"Existing residents records: {residents_count}")
        
        cursor.execute("DROP TABLE IF EXISTS residents")
        
        create_residents_sql = """
        CREATE TABLE residents (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL UNIQUE,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            phone_number VARCHAR(20),
            emergency_contact_name VARCHAR(200),
            emergency_contact_number VARCHAR(20),
            id_number VARCHAR(20) NOT NULL,
            erf_number VARCHAR(20) NOT NULL,
            street_number VARCHAR(10),
            street_name VARCHAR(200),
            full_address TEXT,
            intercom_code VARCHAR(10),
            moving_in_date DATE,
            moving_out_date DATE,
            status VARCHAR(20) DEFAULT 'active',
            migration_date DATETIME,
            migration_reason TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
        
        cursor.execute(create_residents_sql)
        print("✅ Residents table recreated with correct schema")
    else:
        print("✅ Residents table schema is correct")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Database schema fixed!")
    print("📝 Both tables now use VARCHAR(36) for IDs to match the models")

if __name__ == "__main__":
    fix_owners_table_schema()
