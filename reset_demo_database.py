#!/usr/bin/env python3
"""
Reset Demo Database - Clean Start
This script will backup the current database and create a fresh one for clean testing
"""

import sqlite3
import os
import shutil
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'altona_village_cms', 'src', 'database', 'app.db')
BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'database_backups')

def backup_current_database():
    """Backup the current database before deleting"""
    print("🔄 Backing up current database...")
    
    if not os.path.exists(DATABASE_PATH):
        print("❌ No database file found to backup")
        return False
    
    # Create backup directory if it doesn't exist
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Create backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"app_db_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    try:
        shutil.copy2(DATABASE_PATH, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False

def show_current_database_stats():
    """Show current database statistics before deletion"""
    print("\n📊 Current Database Statistics:")
    print("=" * 40)
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Count users
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"Users: {user_count}")
        
        # Count residents
        cursor.execute("SELECT COUNT(*) FROM residents")
        resident_count = cursor.fetchone()[0]
        print(f"Residents: {resident_count}")
        
        # Count owners
        cursor.execute("SELECT COUNT(*) FROM owners")
        owner_count = cursor.fetchone()[0]
        print(f"Owners: {owner_count}")
        
        # Count transition requests
        cursor.execute("SELECT COUNT(*) FROM user_transition_requests")
        transition_count = cursor.fetchone()[0]
        print(f"Transition Requests: {transition_count}")
        
        # Count vehicles
        cursor.execute("SELECT COUNT(*) FROM vehicles")
        vehicle_count = cursor.fetchone()[0]
        print(f"Vehicles: {vehicle_count}")
        
        # Show ERF 8888 specific issues
        print(f"\n🔍 ERF 8888 Issues:")
        cursor.execute("""
            SELECT 'resident' as type, first_name, last_name, status 
            FROM residents WHERE erf_number = 8888 
            UNION ALL
            SELECT 'owner' as type, first_name, last_name, status 
            FROM owners WHERE erf_number = 8888
        """)
        erf_8888_records = cursor.fetchall()
        for record in erf_8888_records:
            type_name, first, last, status = record
            print(f"  • {type_name.title()}: {first} {last} - Status: {status}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error getting database stats: {e}")

def delete_database():
    """Delete the current database file"""
    print(f"\n🗑️  Deleting current database...")
    
    try:
        if os.path.exists(DATABASE_PATH):
            os.remove(DATABASE_PATH)
            print("✅ Database deleted successfully")
            return True
        else:
            print("❌ Database file not found")
            return False
    except Exception as e:
        print(f"❌ Error deleting database: {e}")
        return False

def create_fresh_database():
    """Initialize a fresh database with clean schema"""
    print("\n🆕 Creating fresh database...")
    
    try:
        # The database will be automatically created when the Flask app starts
        # and runs the database initialization
        print("✅ Database will be recreated when the backend starts")
        print("💡 Run the backend server to initialize the fresh database schema")
        return True
    except Exception as e:
        print(f"❌ Error setting up fresh database: {e}")
        return False

def main():
    """Main function to reset the demo database"""
    print("🔄 DEMO DATABASE RESET")
    print("=" * 50)
    print("This will:")
    print("1. Backup the current database")
    print("2. Show current database statistics")
    print("3. Delete the current database")
    print("4. Prepare for fresh database creation")
    print("=" * 50)
    
    # Show current stats
    if os.path.exists(DATABASE_PATH):
        show_current_database_stats()
    
    # Ask for confirmation
    print(f"\n⚠️  WARNING: This will delete the current demo database!")
    print(f"Database path: {DATABASE_PATH}")
    
    confirm = input("\nAre you sure you want to proceed? (yes/no): ").lower().strip()
    
    if confirm != 'yes':
        print("❌ Operation cancelled")
        return False
    
    # Backup current database
    backup_success = backup_current_database()
    if backup_success:
        print("✅ Backup completed")
    
    # Delete current database
    delete_success = delete_database()
    if not delete_success:
        print("❌ Failed to delete database")
        return False
    
    # Setup for fresh database
    fresh_db_success = create_fresh_database()
    if not fresh_db_success:
        print("❌ Failed to setup fresh database")
        return False
    
    print("\n🎉 DATABASE RESET COMPLETED!")
    print("=" * 50)
    print("✅ Old database backed up")
    print("✅ Current database deleted")
    print("✅ Ready for fresh start")
    print("\n📋 Next Steps:")
    print("1. Start the backend server: python altona_village_cms/src/main.py")
    print("2. The fresh database will be automatically created")
    print("3. Create a new admin user to begin testing")
    print("4. Test the user migration functionality with clean data")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
