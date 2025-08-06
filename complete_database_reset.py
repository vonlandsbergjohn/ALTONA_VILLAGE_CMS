#!/usr/bin/env python3
"""
Complete database reset with ALL required columns matching the current models.
"""

import os
import shutil
import sqlite3
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash

def complete_database_reset():
    """Reset database with complete schema matching current models"""
    
    db_path = "altona_village_cms/src/database/app.db"
    backup_dir = "database_backups"
    
    print("🔄 Complete Database Reset")
    print("=" * 60)
    
    # Create backup directory if it doesn't exist
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Backup current database
    if os.path.exists(db_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"app_backup_complete_reset_{timestamp}.db")
        shutil.copy2(db_path, backup_path)
        print(f"✅ Current database backed up to: {backup_path}")
        
        # Remove current database
        os.remove(db_path)
        print("✅ Current database removed")
    
    # Create fresh database
    print("🔨 Creating complete database with all required columns...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table (without unique email constraint for multi-ERF)
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
    
    # Create residents table with ALL columns
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
            moving_in_date DATE,
            moving_out_date DATE,
            status VARCHAR(50) DEFAULT 'active',
            migration_date DATE,
            migration_reason TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE (user_id)
        )
    """)
    
    # Create owners table with ALL columns including the missing ones
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
            intercom_code VARCHAR(10),
            title_deed_number VARCHAR(50),
            acquisition_date DATE,
            postal_street_number VARCHAR(10),
            postal_street_name VARCHAR(200),
            postal_suburb VARCHAR(100),
            postal_city VARCHAR(100),
            postal_code VARCHAR(10),
            postal_province VARCHAR(100),
            full_postal_address TEXT,
            moving_in_date DATE,
            moving_out_date DATE,
            status VARCHAR(50) DEFAULT 'active',
            migration_date DATE,
            migration_reason TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE (user_id)
        )
    """)
    
    # Create all other required tables
    
    # ERF address mappings
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
    
    # Vehicles table
    cursor.execute("""
        CREATE TABLE vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id VARCHAR(36) NOT NULL,
            make VARCHAR(100),
            model VARCHAR(100),
            color VARCHAR(50),
            license_plate VARCHAR(20) NOT NULL,
            year INTEGER,
            vehicle_type VARCHAR(50),
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Communications table
    cursor.execute("""
        CREATE TABLE communications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(200) NOT NULL,
            content TEXT NOT NULL,
            type VARCHAR(50) NOT NULL DEFAULT 'announcement',
            priority VARCHAR(20) NOT NULL DEFAULT 'normal',
            target_audience VARCHAR(100) NOT NULL DEFAULT 'all',
            created_by VARCHAR(36),
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    """)
    
    # Complaints table
    cursor.execute("""
        CREATE TABLE complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id VARCHAR(36) NOT NULL,
            title VARCHAR(200) NOT NULL,
            description TEXT NOT NULL,
            category VARCHAR(100),
            priority VARCHAR(20) NOT NULL DEFAULT 'medium',
            status VARCHAR(50) NOT NULL DEFAULT 'open',
            admin_response TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Transition requests table
    cursor.execute("""
        CREATE TABLE transition_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id VARCHAR(36) NOT NULL,
            request_type VARCHAR(100) NOT NULL,
            current_status VARCHAR(100),
            requested_status VARCHAR(100),
            reason TEXT,
            admin_notes TEXT,
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Changes table
    cursor.execute("""
        CREATE TABLE changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id VARCHAR(36),
            change_type VARCHAR(100) NOT NULL,
            description TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            changed_by VARCHAR(36),
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (changed_by) REFERENCES users (id)
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
    
    # Create admin user
    admin_id = str(uuid.uuid4())
    admin_password_hash = generate_password_hash("admin123")
    
    cursor.execute("""
        INSERT INTO users (id, email, password_hash, role, status)
        VALUES (?, ?, ?, ?, ?)
    """, (admin_id, "admin@altonavillage.com", admin_password_hash, "admin", "active"))
    
    # Create test user with complete resident data
    test_user_id = str(uuid.uuid4())
    test_password_hash = generate_password_hash("test123")
    
    cursor.execute("""
        INSERT INTO users (id, email, password_hash, role, status)
        VALUES (?, ?, ?, ?, ?)
    """, (test_user_id, "test@example.com", test_password_hash, "resident", "active"))
    
    cursor.execute("""
        INSERT INTO residents (user_id, first_name, last_name, id_number, erf_number, 
                              street_number, street_name, full_address, phone_number, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (test_user_id, "Test", "User", "8001010001080", "27627", "28", "Yellowwood Crescent", 
          "28 Yellowwood Crescent, Altona Village, 6850", "+27123456789", "active"))
    
    print("✅ Created complete database schema with ALL columns")
    print("✅ Added sample ERF address mappings")
    print("✅ Created admin user: admin@altonavillage.com / admin123")
    print("✅ Created test user: test@example.com / test123 (ERF 27627)")
    
    conn.commit()
    conn.close()
    
    print("\n🎯 Complete Database Reset Finished!")
    print("=" * 60)
    print("✅ Database now has ALL required columns")
    print("✅ Multi-ERF support enabled (no unique email constraint)")
    print("✅ Ready for comprehensive testing")
    
    return True

if __name__ == "__main__":
    complete_database_reset()
