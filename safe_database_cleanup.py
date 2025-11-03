#!/usr/bin/env python3
"""
Safe database cleanup - check schema first then delete non-admin users.
"""

import psycopg2
import os

DATABASE_URL = os.getenv('DATABASE_URL', "postgresql://postgres:%23Johnvonl1977@localhost:5432/altona_village_db")

def safe_cleanup_database():
    """Safely delete all users except admin after checking schema"""
    
    print("🧹 Safe Database Cleanup")
    print("=" * 50)
    
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Check what tables exist
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [table[0] for table in cursor.fetchall()]
        print(f"📋 Available tables: {', '.join(tables)}")
        
        # Get current users
        cursor.execute("SELECT id, email, role, status FROM users")
        all_users = cursor.fetchall()
        
        print(f"\n👥 Current Users ({len(all_users)}):")
        admin_users = []
        non_admin_users = []
        
        for user in all_users:
            print(f"  {user[1]} - {user[2]} - {user[3]}")
            if user[2] == 'admin':
                admin_users.append(user)
            else:
                non_admin_users.append(user)
        
        if not non_admin_users:
            print("✅ No non-admin users found. Database is already clean.")
            return
        
        non_admin_user_ids = tuple([str(user[0]) for user in non_admin_users])
        
        print(f"\n🗑️ Will delete {len(non_admin_users)} non-admin users and their data...")
        
        # Delete in correct order (foreign key constraints)
        
        # 1. Delete vehicles
        if 'vehicles' in tables:
            cursor.execute("""
                DELETE FROM vehicles 
                WHERE resident_id IN (SELECT id FROM residents WHERE user_id = ANY(%s))
            """, (list(non_admin_user_ids),))
            vehicles_by_residents = cursor.rowcount
            
            cursor.execute("""
                DELETE FROM vehicles 
                WHERE owner_id IN (SELECT id FROM owners WHERE user_id = ANY(%s))
            """, (list(non_admin_user_ids),))
            vehicles_by_owners = cursor.rowcount
            
            print(f"  ✅ Deleted {vehicles_by_residents + vehicles_by_owners} vehicles")
        
        # 2. Delete complaints
        if 'complaints' in tables:
            cursor.execute("""
                DELETE FROM complaints 
                WHERE resident_id IN (SELECT id FROM residents WHERE user_id = ANY(%s))
            """, (list(non_admin_user_ids),))
            print(f"  ✅ Deleted {cursor.rowcount} complaints")
        
        # 3. Delete complaint updates
        if 'complaint_updates' in tables:
            # Assuming complaint_updates are linked via complaints table
            print("  ✅ Skipping complaint_updates deletion (cascades from complaints)")

        # 4. Delete residents
        if 'residents' in tables:
            cursor.execute("DELETE FROM residents WHERE user_id = ANY(%s)", (list(non_admin_user_ids),))
            print(f"  ✅ Deleted {cursor.rowcount} residents")
        
        # 5. Delete owners
        if 'owners' in tables:
            cursor.execute("DELETE FROM owners WHERE user_id = ANY(%s)", (list(non_admin_user_ids),))
            print(f"  ✅ Deleted {cursor.rowcount} owners")
        
        # 6. Delete user change logs
        if 'user_changes' in tables:
            cursor.execute("DELETE FROM user_changes WHERE user_id = ANY(%s)", (list(non_admin_user_ids),))
            print(f"  ✅ Deleted {cursor.rowcount} user change logs")
        
        # 7. Delete pending registrations
        if 'pending_registrations' in tables:
            user_emails = tuple([user[1] for user in non_admin_users])
            cursor.execute("DELETE FROM pending_registrations WHERE email = ANY(%s)", (list(user_emails),))
            print(f"  ✅ Deleted {cursor.rowcount} pending registrations")
        
        # 8. Finally, delete the users
        cursor.execute("DELETE FROM users WHERE id = ANY(%s)", (list(non_admin_user_ids),))
        print(f"  ✅ Deleted {cursor.rowcount} users")
        
        conn.commit()
        
        # Verify cleanup
        print("\n✅ Verification - Remaining Users:")
        cursor.execute("SELECT id, email, role, status FROM users")
        remaining_users = cursor.fetchall()
        
        if remaining_users:
            for user in remaining_users:
                print(f"  {user[1]} - {user[2]} - {user[3]}")
        else:
            print("  ❌ NO USERS FOUND - This shouldn't happen!")
        
        # Check data counts
        for table in ['residents', 'owners', 'vehicles']:
            if table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table}: {count} records")
        
        print("\n🎉 Database cleanup complete!")
        print("   Ready for fresh user registrations.")

    except Exception as e:
        print(f"An error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    safe_cleanup_database()
