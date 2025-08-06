#!/usr/bin/env python3
"""
Reset database for fresh testing of multi-ERF functionality.
This will backup the current database and create a clean test environment.
"""

import os
import shutil
import sqlite3
from datetime import datetime

def reset_database_for_testing():
    """Reset database and create fresh test data"""
    
    db_path = "altona_village_cms/src/database/app.db"
    backup_dir = "database_backups"
    
    print("🔄 Resetting Database for Multi-ERF Testing")
    print("=" * 60)
    
    # Create backup directory if it doesn't exist
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Backup current database
    if os.path.exists(db_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"app_backup_multi_erf_test_{timestamp}.db")
        shutil.copy2(db_path, backup_path)
        print(f"✅ Current database backed up to: {backup_path}")
        
        # Remove current database
        os.remove(db_path)
        print("✅ Current database removed")
    
    # Create fresh database
    print("🔨 Creating fresh database with test data...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table (without unique email constraint)
    cursor.execute("""
        CREATE TABLE users (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL DEFAULT 'resident',
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            approval_email_sent BOOLEAN DEFAULT 0,
            approval_email_sent_at DATETIME,
            rejection_email_sent BOOLEAN DEFAULT 0,
            rejection_email_sent_at DATETIME,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create residents table
    cursor.execute("""
        CREATE TABLE residents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id VARCHAR(36) NOT NULL,
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
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE (user_id)
        )
    """)
    
    # Create owners table
    cursor.execute("""
        CREATE TABLE owners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id VARCHAR(36) NOT NULL,
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
            full_postal_address TEXT,
            title_deed_number VARCHAR(50),
            intercom_code VARCHAR(10),
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE (user_id)
        )
    """)
    
    # Create ERF address mappings table
    cursor.execute("""
        CREATE TABLE erf_address_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            erf_number VARCHAR(20) NOT NULL UNIQUE,
            street_number VARCHAR(10),
            street_name VARCHAR(200),
            full_address TEXT NOT NULL,
            postal_code VARCHAR(10),
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert sample ERF mappings
    sample_erfs = [
        ('27626', '26', 'Yellowwood Crescent', '26 Yellowwood Crescent, Altona Village, 6850', '6850'),
        ('27627', '28', 'Yellowwood Crescent', '28 Yellowwood Crescent, Altona Village, 6850', '6850'),
        ('12345', '10', 'Oak Street', '10 Oak Street, Altona Village, 6850', '6850'),
        ('67890', '25', 'Pine Avenue', '25 Pine Avenue, Altona Village, 6850', '6850'),
        ('11111', '15', 'Maple Drive', '15 Maple Drive, Altona Village, 6850', '6850'),
        ('22222', '30', 'Birch Lane', '30 Birch Lane, Altona Village, 6850', '6850'),
        ('33333', '45', 'Cedar Close', '45 Cedar Close, Altona Village, 6850', '6850')
    ]
    
    cursor.executemany("""
        INSERT INTO erf_address_mappings (erf_number, street_number, street_name, full_address, postal_code)
        VALUES (?, ?, ?, ?, ?)
    """, sample_erfs)
    
    print("✅ Created fresh database schema")
    print("✅ Added sample ERF address mappings")
    
    conn.commit()
    conn.close()
    
    print("\n📊 Database Reset Complete!")
    print("=" * 60)
    print("✅ Fresh database created with multi-ERF support")
    print("✅ Email unique constraint removed")
    print("✅ Sample ERF addresses loaded")
    print("\nYou can now:")
    print("1. Restart the backend server")
    print("2. Test multi-ERF registrations with same email")
    print("3. Create comprehensive test scenarios")
    
    return True

if __name__ == "__main__":
    reset_database_for_testing()
