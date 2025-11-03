#!/usr/bin/env python3
"""
Reset Demo Database - Clean Start
This script will backup the current database and create a fresh one for clean testing
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from datetime import datetime
import subprocess

DB_NAME = "altona_village_db"
DB_USER = "postgres"
DB_PASS = os.getenv("PGPASSWORD", "#Johnvonl1977") # Use env var if available
DB_HOST = "localhost"
DB_PORT = "5432"

ADMIN_DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/postgres"
TARGET_DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'database_backups')

def backup_current_database():
    """Backup the current database before deleting"""
    print("🔄 Backing up current database...")
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{DB_NAME}_backup_{timestamp}.sql"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    command = [
        'pg_dump',
        '--dbname=' + TARGET_DB_URL,
        '-f', backup_path,
        '--clean',
        '--if-exists'
    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ Database backed up to: {backup_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Backup failed. pg_dump is required in your system's PATH.")
        print(f"   Error: {e.stderr}")
        return False

def drop_and_recreate_database():
    """Drops and recreates the database."""
    print(f"\n🗑️  Dropping and recreating database '{DB_NAME}'...")
    conn = None
    try:
        conn = psycopg2.connect(ADMIN_DB_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME};")
        print(f"   ✅ Dropped database '{DB_NAME}'.")
        cursor.execute(f"CREATE DATABASE {DB_NAME};")
        print(f"   ✅ Created database '{DB_NAME}'.")
        return True
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        print("   💡 Make sure the user '{DB_USER}' has privileges to create databases.")
        return False
    finally:
        if conn:
            conn.close()

def main():
    """Main function to reset the demo database"""
    print("🔄 DEMO DATABASE RESET")
    print("=" * 50)
    print("This will:")
    print(f"1. Backup the '{DB_NAME}' database using pg_dump")
    print(f"2. Drop the '{DB_NAME}' database")
    print(f"3. Re-create the '{DB_NAME}' database")
    print("=" * 50)
    
    # Ask for confirmation
    print(f"\n⚠️  WARNING: This will PERMANENTLY delete and recreate the '{DB_NAME}' database!")
    
    confirm = input("\nAre you sure you want to proceed? (yes/no): ").lower().strip()
    
    if confirm != 'yes':
        print("❌ Operation cancelled")
        return
    
    # Backup current database
    if not backup_current_database():
        confirm_continue = input("\nBackup failed. Continue with deletion anyway? (yes/no): ").lower().strip()
        if confirm_continue != 'yes':
            print("❌ Operation cancelled")
            return
    
    # Drop and recreate
    if not drop_and_recreate_database():
        print("❌ Failed to reset database.")
        return
    
    print("\n🎉 DATABASE RESET COMPLETED!")
    print("=" * 50)
    print("✅ Old database backed up")
    print(f"✅ Database '{DB_NAME}' has been reset")
    print("✅ Ready for fresh start")
    print("\n📋 Next Steps:")
    print("1. Run the Flask application to initialize the schema (db.create_all()).")
    print("   (e.g., `python altona_village_cms/src/main.py`)")
    print("2. Run any data seeding scripts (e.g., to create an admin user).")

if __name__ == "__main__":
    main()
