#!/usr/bin/env python3
"""
Add missing tables and admin user to the fresh database.
"""

import sqlite3
import uuid
from werkzeug.security import generate_password_hash

def setup_complete_database():
    """Add missing tables and create admin user"""
    
    db_path = "altona_village_cms/src/database/app.db"
    
    print("🔧 Setting up complete database...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if we need additional tables that might be missing
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in cursor.fetchall()]
    print(f"Existing tables: {existing_tables}")
    
    # Create additional tables that might be needed
    tables_to_create = []
    
    # Vehicles table
    if 'vehicles' not in existing_tables:
        tables_to_create.append('vehicles')
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
    if 'communications' not in existing_tables:
        tables_to_create.append('communications')
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
    if 'complaints' not in existing_tables:
        tables_to_create.append('complaints')
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
    if 'transition_requests' not in existing_tables:
        tables_to_create.append('transition_requests')
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
    
    # Changes table for admin tracking
    if 'changes' not in existing_tables:
        tables_to_create.append('changes')
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
    
    if tables_to_create:
        print(f"✅ Created missing tables: {', '.join(tables_to_create)}")
    
    # Create an admin user
    admin_id = str(uuid.uuid4())
    admin_password_hash = generate_password_hash("admin123")
    
    cursor.execute("""
        INSERT INTO users (id, email, password_hash, role, status)
        VALUES (?, ?, ?, ?, ?)
    """, (admin_id, "admin@altonavillage.com", admin_password_hash, "admin", "active"))
    
    print("✅ Created admin user: admin@altonavillage.com / admin123")
    
    # Create a test user with ERF data for immediate testing
    test_user_id = str(uuid.uuid4())
    test_password_hash = generate_password_hash("test123")
    
    cursor.execute("""
        INSERT INTO users (id, email, password_hash, role, status)
        VALUES (?, ?, ?, ?, ?)
    """, (test_user_id, "test@example.com", test_password_hash, "resident", "active"))
    
    cursor.execute("""
        INSERT INTO residents (user_id, first_name, last_name, id_number, erf_number, 
                              street_number, street_name, full_address, phone_number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (test_user_id, "Test", "User", "8001010001080", "27627", "28", "Yellowwood Crescent", 
          "28 Yellowwood Crescent, Altona Village, 6850", "+27123456789"))
    
    print("✅ Created test user: test@example.com / test123 (ERF 27627)")
    
    conn.commit()
    conn.close()
    
    print("\n🎯 Database Setup Complete!")
    print("=" * 50)
    print("You can now login with:")
    print("  Admin: admin@altonavillage.com / admin123")
    print("  Test User: test@example.com / test123")
    print("\nThe app should work properly now!")

if __name__ == "__main__":
    setup_complete_database()
