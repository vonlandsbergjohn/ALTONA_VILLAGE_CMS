#!/usr/bin/env python3
"""
User Archive Management Interface
Interactive tool for managing user archival and deletion
"""

from user_archive_deletion_system import UserArchiveDeletionSystem
import sys

def main():
    """Interactive management interface"""
    system = UserArchiveDeletionSystem()
    
    print("🏠 ALTONA VILLAGE CMS - USER ARCHIVE MANAGEMENT")
    print("=" * 60)
    
    while True:
        print("\nSelect an option:")
        print("1. Analyze inactive users")
        print("2. Archive a specific user")
        print("3. View archived users")
        print("4. Clean up old archives")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            analyze_inactive_users(system)
        elif choice == "2":
            archive_specific_user(system)
        elif choice == "3":
            view_archived_users(system)
        elif choice == "4":
            cleanup_old_archives(system)
        elif choice == "5":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

def analyze_inactive_users(system):
    """Analyze and display inactive users"""
    print("\n🔍 ANALYZING INACTIVE USERS...")
    print("-" * 40)
    
    try:
        inactive_users = system.get_inactive_users_analysis()
        
        if not inactive_users:
            print("✅ No inactive users found requiring archive action.")
            return
        
        print(f"\n📊 Found {len(inactive_users)} inactive users:")
        
        for i, user in enumerate(inactive_users, 1):
            print(f"\n{i}. {user['email']} ({user['user_type']})")
            print(f"   Status: {user['user_status']}")
            print(f"   Recommended Action: {user['recommended_action']}")
            print(f"   Retention Period: {user['retention_period']}")
            
            if user['vehicles']:
                print(f"   Vehicles: {len(user['vehicles'])}")
            if user['complaints']:
                print(f"   Complaints: {len(user['complaints'])}")
        
        # Offer to archive users
        print(f"\n🗄️ Would you like to archive any of these users?")
        response = input("Enter user number to archive, or 'n' to skip: ").strip().lower()
        
        if response != 'n' and response.isdigit():
            user_index = int(response) - 1
            if 0 <= user_index < len(inactive_users):
                user_to_archive = inactive_users[user_index]
                confirm_and_archive_user(system, user_to_archive)
            else:
                print("❌ Invalid user number.")
    
    except Exception as e:
        print(f"❌ Error analyzing users: {e}")

def archive_specific_user(system):
    """Archive a specific user by email"""
    print("\n🗄️ ARCHIVE SPECIFIC USER")
    print("-" * 30)
    
    email = input("Enter user email to archive: ").strip()
    if not email:
        print("❌ Email cannot be empty.")
        return
    
    reason = input("Enter archive reason: ").strip()
    if not reason:
        reason = "Manual archive via management interface"
    
    admin_id = input("Enter admin user ID (or press Enter for system): ").strip()
    if not admin_id:
        admin_id = "system"
    
    # Find user by email
    try:
        conn = system.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        user_result = cursor.fetchone()
        
        if not user_result:
            print(f"❌ User with email '{email}' not found.")
            conn.close()
            return
        
        user_id = user_result[0]
        conn.close()
        
        print(f"\n📋 User found: {email}")
        confirm = input("Are you sure you want to archive this user? (y/N): ").strip().lower()
        
        if confirm == 'y':
            success = system.archive_user(user_id, reason, admin_id)
            if success:
                print("✅ User archived successfully!")
            else:
                print("❌ Failed to archive user.")
        else:
            print("ℹ️ Archive cancelled.")
    
    except Exception as e:
        print(f"❌ Error archiving user: {e}")

def confirm_and_archive_user(system, user_data):
    """Confirm and archive a user"""
    print(f"\n📋 Archive User: {user_data['email']}")
    print(f"   Type: {user_data['user_type']}")
    print(f"   Action: {user_data['recommended_action']}")
    print(f"   Retention: {user_data['retention_period']}")
    
    confirm = input("\nAre you sure you want to archive this user? (y/N): ").strip().lower()
    
    if confirm == 'y':
        reason = input("Enter archive reason (or press Enter for default): ").strip()
        if not reason:
            reason = f"Automated archive - {user_data['recommended_action']}"
        
        admin_id = input("Enter admin user ID (or press Enter for system): ").strip()
        if not admin_id:
            admin_id = "system"
        
        success = system.archive_user(user_data['user_id'], reason, admin_id)
        if success:
            print("✅ User archived successfully!")
        else:
            print("❌ Failed to archive user.")
    else:
        print("ℹ️ Archive cancelled.")

def view_archived_users(system):
    """View all archived users"""
    print("\n📦 VIEWING ARCHIVED USERS")
    print("-" * 30)
    
    try:
        archived_users = system.get_archived_users()
        
        if not archived_users:
            print("ℹ️ No archived users found.")
            return
        
        print(f"Found {len(archived_users)} archived users:")
        
        for archive in archived_users:
            print(f"\n📦 {archive[7] or 'Unknown Email'}")
            print(f"   User Type: {archive[5]}")
            print(f"   Archived: {archive[2][:19]}")
            print(f"   Reason: {archive[4]}")
            print(f"   Policy: {archive[6]}")
    
    except Exception as e:
        print(f"❌ Error viewing archived users: {e}")

def cleanup_old_archives(system):
    """Clean up old archive records"""
    print("\n🧹 CLEAN UP OLD ARCHIVES")
    print("-" * 30)
    
    try:
        days = input("Enter retention days (default 730 = 2 years): ").strip()
        if not days.isdigit():
            days = 730
        else:
            days = int(days)
        
        confirm = input(f"Delete archive records older than {days} days? (y/N): ").strip().lower()
        
        if confirm == 'y':
            deleted_count = system.cleanup_old_archives(days)
            print(f"✅ Cleaned up {deleted_count} old archive records.")
        else:
            print("ℹ️ Cleanup cancelled.")
    
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

if __name__ == "__main__":
    main()
