#!/usr/bin/env python3
"""
Delete all users except admin user and clean up related data.
"""

import sqlite3

def clean_database_except_admin():
    """Delete all users except admin and their related data"""
    
    db_path = "altona_village_cms/src/database/app.db"
    
    print("🧹 Cleaning Database (Keeping Admin Only)")
    print("=" * 50)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # First, check what users we have
    cursor.execute("SELECT id, email, role, status FROM users")
    all_users = cursor.fetchall()
    
    print("📊 Current Users:")
    admin_users = []
    non_admin_users = []
    
    for user in all_users:
        print(f"  {user[1]} - {user[2]} - {user[3]}")
        if user[2] == 'admin':
            admin_users.append(user)
        else:
            non_admin_users.append(user)
    
    print(f"\nAdmin users to keep: {len(admin_users)}")
    print(f"Non-admin users to delete: {len(non_admin_users)}")
    
    if not non_admin_users:
        print("✅ No non-admin users found. Database is already clean.")
        conn.close()
        return
    
    # Get user IDs to delete
    non_admin_user_ids = [user[0] for user in non_admin_users]
    user_ids_placeholder = ','.join(['?' for _ in non_admin_user_ids])
    
    print("\n🗑️ Deleting Related Data...")
    
    # Delete vehicles owned by residents/owners of non-admin users
    cursor.execute(f"""
        DELETE FROM vehicles 
        WHERE resident_id IN (
            SELECT id FROM residents WHERE user_id IN ({user_ids_placeholder})
        ) OR owner_id IN (
            SELECT id FROM owners WHERE user_id IN ({user_ids_placeholder})
        )
    """, non_admin_user_ids + non_admin_user_ids)
    deleted_vehicles = cursor.rowcount
    print(f"  ✅ Deleted {deleted_vehicles} vehicles")
    
    # Delete complaints from non-admin users
    cursor.execute(f"""
        DELETE FROM complaints 
        WHERE user_id IN ({user_ids_placeholder})
    """, non_admin_user_ids)
    deleted_complaints = cursor.rowcount
    print(f"  ✅ Deleted {deleted_complaints} complaints")
    
    # Delete complaint updates from non-admin users
    cursor.execute(f"""
        DELETE FROM complaint_updates 
        WHERE user_id IN ({user_ids_placeholder})
    """, non_admin_user_ids)
    deleted_updates = cursor.rowcount
    print(f"  ✅ Deleted {deleted_updates} complaint updates")
    
    # Delete residents
    cursor.execute(f"""
        DELETE FROM residents 
        WHERE user_id IN ({user_ids_placeholder})
    """, non_admin_user_ids)
    deleted_residents = cursor.rowcount
    print(f"  ✅ Deleted {deleted_residents} residents")
    
    # Delete owners
    cursor.execute(f"""
        DELETE FROM owners 
        WHERE user_id IN ({user_ids_placeholder})
    """, non_admin_user_ids)
    deleted_owners = cursor.rowcount
    print(f"  ✅ Deleted {deleted_owners} owners")
    
    # Delete user change logs for non-admin users
    try:
        cursor.execute(f"""
            DELETE FROM user_changes 
            WHERE user_id IN ({user_ids_placeholder})
        """, non_admin_user_ids)
        deleted_logs = cursor.rowcount
        print(f"  ✅ Deleted {deleted_logs} user change logs")
    except sqlite3.OperationalError:
        print("  ℹ️ User changes table not found (skipping)")
    
    # Delete pending registrations for non-admin users
    try:
        cursor.execute(f"""
            DELETE FROM pending_registrations 
            WHERE email IN (
                SELECT email FROM users WHERE id IN ({user_ids_placeholder})
            )
        """, non_admin_user_ids)
        deleted_pending = cursor.rowcount
        print(f"  ✅ Deleted {deleted_pending} pending registrations")
    except sqlite3.OperationalError:
        print("  ℹ️ Pending registrations table not found (skipping)")
    
    # Finally, delete the non-admin users
    cursor.execute(f"""
        DELETE FROM users 
        WHERE id IN ({user_ids_placeholder})
    """, non_admin_user_ids)
    deleted_users = cursor.rowcount
    print(f"  ✅ Deleted {deleted_users} users")
    
    conn.commit()
    
    # Verify cleanup
    print("\n✅ Verification - Remaining Users:")
    cursor.execute("SELECT id, email, role, status FROM users")
    remaining_users = cursor.fetchall()
    
    for user in remaining_users:
        print(f"  {user[1]} - {user[2]} - {user[3]}")
    
    # Check remaining data counts
    cursor.execute("SELECT COUNT(*) FROM residents")
    remaining_residents = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM owners")
    remaining_owners = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM vehicles")
    remaining_vehicles = cursor.fetchone()[0]
    
    print(f"\nRemaining data:")
    print(f"  Users: {len(remaining_users)}")
    print(f"  Residents: {remaining_residents}")
    print(f"  Owners: {remaining_owners}")
    print(f"  Vehicles: {remaining_vehicles}")
    
    conn.close()
    
    print("\n🎉 Database cleanup complete! Only admin users remain.")
    print("   You can now register fresh users for testing.")

if __name__ == "__main__":
    clean_database_except_admin()
