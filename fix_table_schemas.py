#!/usr/bin/env python3
"""
Fix the owners table schema to match the model definition.
"""

import psycopg2
import os

DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://postgres:%23Johnvonl1977@localhost:5432/altona_village_db")

def fix_owners_table_schema():
    """Fix the owners table to match the Owner model"""
    
    print("🔧 Fixing Owners Table Schema")
    print("=" * 40)
    
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Check if we have any existing data
        cursor.execute("SELECT COUNT(*) FROM owners")
        existing_count = cursor.fetchone()[0]
        print(f"Existing owners records: {existing_count}")
        
        if existing_count > 0:
            print("⚠️  Existing data found. This script will drop and recreate tables.")
        
        # Drop and recreate the owners table with correct schema
        print("🗑️  Dropping existing owners table...")
        cursor.execute("DROP TABLE IF EXISTS owners CASCADE")
        
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
            migration_date TIMESTAMP,
            migration_reason TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
        cursor.execute(create_table_sql)
        
        # Also fix the residents table while we're at it
        print("\n🔧 Fixing residents table schema...")
        cursor.execute("DROP TABLE IF EXISTS residents CASCADE")
        
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
            migration_date TIMESTAMP,
            migration_reason TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
        cursor.execute(create_residents_sql)
        print("✅ Residents table recreated with correct schema")
        
        conn.commit()
        
        print("\n✅ Database schema fixed!")
        print("📝 Both tables now use VARCHAR(36) for IDs to match the models")

    except Exception as e:
        print(f"An error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_owners_table_schema()
