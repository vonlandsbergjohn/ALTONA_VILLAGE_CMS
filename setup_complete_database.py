#!/usr/bin/env python3
"""
Add missing tables and admin user to the fresh database.
"""

import psycopg2
import os
import uuid
from werkzeug.security import generate_password_hash

DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://postgres:%23Johnvonl1977@localhost:5432/altona_village_db")

def setup_complete_database():
    """Add missing tables and create admin user"""
    
    print("🔧 Setting up complete database...")
    
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Check if we need additional tables that might be missing
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        print(f"Existing tables: {existing_tables}")
        
        # Create additional tables that might be needed
        tables_to_create = []
        
        # Users table (MUST be created first)
        if 'users' not in existing_tables:
            tables_to_create.append('users')
            cursor.execute("""
                CREATE TABLE users (
                    id VARCHAR(36) PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(50) NOT NULL DEFAULT 'pending',
                    status VARCHAR(50) NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    archived BOOLEAN DEFAULT FALSE,
                    archived_at TIMESTAMP,
                    archived_by VARCHAR(36)
                )
            """)

        # Residents table
        if 'residents' not in existing_tables:
            tables_to_create.append('residents')
            cursor.execute("""
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
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)

        # Owners table
        if 'owners' not in existing_tables:
            tables_to_create.append('owners')
            cursor.execute("""
                CREATE TABLE owners (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL UNIQUE,
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) NOT NULL,
                    erf_number VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'active',
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)

        # Vehicles table
        if 'vehicles' not in existing_tables:
            tables_to_create.append('vehicles')
            cursor.execute("""
                CREATE TABLE vehicles (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL,
                    make VARCHAR(100),
                    model VARCHAR(100),
                    color VARCHAR(50),
                    license_plate VARCHAR(20) NOT NULL,
                    year INTEGER,
                    vehicle_type VARCHAR(50),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
        
        # Communications table
        if 'communications' not in existing_tables:
            tables_to_create.append('communications')
            cursor.execute("""
                CREATE TABLE communications (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(200) NOT NULL,
                    content TEXT NOT NULL,
                    type VARCHAR(50) NOT NULL DEFAULT 'announcement',
                    priority VARCHAR(20) NOT NULL DEFAULT 'normal',
                    target_audience VARCHAR(100) NOT NULL DEFAULT 'all',
                    created_by VARCHAR(36),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            """)
        
        # Complaints table
        if 'complaints' not in existing_tables:
            tables_to_create.append('complaints')
            cursor.execute("""
                CREATE TABLE complaints (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    description TEXT NOT NULL,
                    category VARCHAR(100),
                    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
                    status VARCHAR(50) NOT NULL DEFAULT 'open',
                    admin_response TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
        
        # Transition requests table (simplified version)
        if 'user_transition_requests' not in existing_tables:
            tables_to_create.append('user_transition_requests')
            cursor.execute("""
                CREATE TABLE user_transition_requests (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36),
                    request_type VARCHAR(100) NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
        
        # Changes table for admin tracking
        if 'user_changes' not in existing_tables:
            tables_to_create.append('user_changes')
            cursor.execute("""
                CREATE TABLE user_changes (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(36),
                    change_type VARCHAR(100) NOT NULL,
                    description TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    changed_by VARCHAR(36),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
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
            VALUES (%s, %s, %s, %s, %s) ON CONFLICT (email) DO NOTHING;
        """, (admin_id, "admin@altonavillage.com", admin_password_hash, "admin", "active"))
        
        print("✅ Ensured admin user exists: admin@altonavillage.com / admin123")
        
        # Create a test user with ERF data for immediate testing
        test_user_id = str(uuid.uuid4())
        test_password_hash = generate_password_hash("test123")
        
        cursor.execute("""
            INSERT INTO users (id, email, password_hash, role, status)
            VALUES (%s, %s, %s, %s, %s) ON CONFLICT (email) DO NOTHING;
        """, (test_user_id, "test@example.com", test_password_hash, "resident", "active"))
        
        # Use the ID of the user that was actually inserted or already existed
        cursor.execute("SELECT id FROM users WHERE email = %s", ("test@example.com",))
        actual_test_user_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO residents (id, user_id, first_name, last_name, id_number, erf_number, 
                                  street_number, street_name, full_address, phone_number)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (user_id) DO NOTHING;
        """, (str(uuid.uuid4()), actual_test_user_id, "Test", "User", "8001010001080", "27627", "28", "Yellowwood Crescent", 
              "28 Yellowwood Crescent, Altona Village, 6850", "+27123456789"))
        
        print("✅ Ensured test user exists: test@example.com / test123 (ERF 27627)")
        
        conn.commit()
        
        print("\n🎯 Database Setup Complete!")
        print("=" * 50)
        print("You can now login with:")
        print("  Admin: admin@altonavillage.com / admin123")
        print("  Test User: test@example.com / test123")
        print("\nThe app should work properly now!")

    except Exception as e:
        print(f"An error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    setup_complete_database()
