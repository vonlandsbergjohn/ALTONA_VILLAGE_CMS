#!/usr/bin/env python3
"""
Admin Permanent User Deletion Tool
For removing users who were incorrectly approved or mistakenly registered
"""

import sys
import os
from user_archive_deletion_system import UserArchiveDeletionSystem

class AdminDeletionTool:
    def __init__(self):
        self.system = UserArchiveDeletionSystem()
    
    def list_all_users(self):
        """List all users for admin to choose from"""
        conn = self.system.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.id, u.email, u.role, u.status, u.created_at,
                   r.first_name as resident_first, r.last_name as resident_last, r.erf_number as resident_erf,
                   o.first_name as owner_first, o.last_name as owner_last, o.erf_number as owner_erf
            FROM users u
            LEFT JOIN residents r ON u.id = r.user_id
            LEFT JOIN owners o ON u.id = o.user_id
            ORDER BY u.created_at DESC
        """)
        
        users = cursor.fetchall()
        conn.close()
        
        print("\n📋 ALL USERS IN SYSTEM")
        print("=" * 80)
        print(f"{'#':<3} {'Email':<30} {'Role':<15} {'Name':<25} {'ERF':<8} {'Status':<12} {'Created':<12}")
        print("-" * 80)
        
        for i, user in enumerate(users, 1):
            user_id, email, role, status, created_at = user[:5]
            resident_first, resident_last, resident_erf = user[5:8]
            owner_first, owner_last, owner_erf = user[8:11]
            
            # Determine display name and ERF
            if resident_first:
                name = f"{resident_first} {resident_last}"
                erf = resident_erf or ""
            elif owner_first:
                name = f"{owner_first} {owner_last}"
                erf = owner_erf or ""
            else:
                name = "No profile"
                erf = ""
            
            created_date = created_at[:10] if created_at else "Unknown"
            
            print(f"{i:<3} {email:<30} {role:<15} {name:<25} {erf:<8} {status:<12} {created_date:<12}")
        
        return users
    
    def search_user(self, search_term):
        """Search for users by email or name"""
        conn = self.system.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.id, u.email, u.role, u.status, u.created_at,
                   r.first_name as resident_first, r.last_name as resident_last, r.erf_number as resident_erf,
                   o.first_name as owner_first, o.last_name as owner_last, o.erf_number as owner_erf
            FROM users u
            LEFT JOIN residents r ON u.id = r.user_id
            LEFT JOIN owners o ON u.id = o.user_id
            WHERE u.email LIKE ? 
               OR r.first_name LIKE ? 
               OR r.last_name LIKE ?
               OR o.first_name LIKE ?
               OR o.last_name LIKE ?
            ORDER BY u.created_at DESC
        """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
        
        users = cursor.fetchall()
        conn.close()
        
        if users:
            print(f"\n🔍 SEARCH RESULTS FOR: '{search_term}'")
            print("=" * 80)
            print(f"{'#':<3} {'Email':<30} {'Role':<15} {'Name':<25} {'ERF':<8} {'Status':<12}")
            print("-" * 80)
            
            for i, user in enumerate(users, 1):
                user_id, email, role, status, created_at = user[:5]
                resident_first, resident_last, resident_erf = user[5:8]
                owner_first, owner_last, owner_erf = user[8:11]
                
                if resident_first:
                    name = f"{resident_first} {resident_last}"
                    erf = resident_erf or ""
                elif owner_first:
                    name = f"{owner_first} {owner_last}"
                    erf = owner_erf or ""
                else:
                    name = "No profile"
                    erf = ""
                
                print(f"{i:<3} {email:<30} {role:<15} {name:<25} {erf:<8} {status:<12}")
        else:
            print(f"\n❌ No users found matching: '{search_term}'")
        
        return users
    
    def get_user_details(self, user_id):
        """Get detailed information about a specific user"""
        conn = self.system.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.id, u.email, u.role, u.status, u.created_at, u.last_login,
                   r.first_name as resident_first, r.last_name as resident_last, 
                   r.erf_number as resident_erf, r.phone_number as resident_phone,
                   r.status as resident_status,
                   o.first_name as owner_first, o.last_name as owner_last,
                   o.erf_number as owner_erf, o.phone_number as owner_phone,
                   o.status as owner_status
            FROM users u
            LEFT JOIN residents r ON u.id = r.user_id
            LEFT JOIN owners o ON u.id = o.user_id
            WHERE u.id = ?
        """, (user_id,))
        
        user_data = cursor.fetchone()
        
        if not user_data:
            print(f"❌ User {user_id} not found")
            return None
        
        # Get related data counts
        cursor.execute("SELECT COUNT(*) FROM vehicles WHERE resident_id = ? OR owner_id = ?", (user_id, user_id))
        vehicle_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM complaints WHERE resident_id = ?", (user_id,))
        complaint_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM user_transition_requests WHERE user_id = ?", (user_id,))
        transition_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"\n👤 USER DETAILS")
        print("=" * 50)
        print(f"Email: {user_data[1]}")
        print(f"Role: {user_data[2]}")
        print(f"Status: {user_data[3]}")
        print(f"Created: {user_data[4]}")
        print(f"Last Login: {user_data[5] or 'Never'}")
        
        if user_data[6]:  # Has resident profile
            print(f"\n🏠 RESIDENT PROFILE:")
            print(f"   Name: {user_data[6]} {user_data[7]}")
            print(f"   ERF: {user_data[8]}")
            print(f"   Phone: {user_data[9] or 'Not provided'}")
            print(f"   Status: {user_data[10]}")
        
        if user_data[11]:  # Has owner profile
            print(f"\n🏡 OWNER PROFILE:")
            print(f"   Name: {user_data[11]} {user_data[12]}")
            print(f"   ERF: {user_data[13]}")
            print(f"   Phone: {user_data[14] or 'Not provided'}")
            print(f"   Status: {user_data[15]}")
        
        print(f"\n📊 RELATED DATA:")
        print(f"   Vehicles: {vehicle_count}")
        print(f"   Complaints: {complaint_count}")
        print(f"   Transition Requests: {transition_count}")
        
        return user_data
    
    def confirm_deletion(self, user_email):
        """Get admin confirmation for deletion"""
        print(f"\n⚠️  PERMANENT DELETION CONFIRMATION")
        print("=" * 50)
        print(f"You are about to PERMANENTLY DELETE user: {user_email}")
        print("")
        print("⚠️  WARNING: This action cannot be undone!")
        print("   All user data will be permanently removed from the system.")
        print("   This should only be used for:")
        print("   - Incorrectly approved registrations")
        print("   - Mistaken registrations")
        print("   - Users who should never have been in the system")
        print("")
        
        confirm1 = input("Type 'DELETE' to confirm (case sensitive): ")
        if confirm1 != "DELETE":
            print("❌ Deletion cancelled")
            return False
        
        confirm2 = input(f"Type the user's email '{user_email}' to confirm: ")
        if confirm2 != user_email:
            print("❌ Email confirmation failed. Deletion cancelled")
            return False
        
        deletion_reason = input("Enter reason for deletion: ").strip()
        if not deletion_reason:
            print("❌ Deletion reason is required. Deletion cancelled")
            return False
        
        return deletion_reason
    
    def interactive_deletion(self):
        """Interactive tool for admin to delete users"""
        print("🗑️ ADMIN PERMANENT USER DELETION TOOL")
        print("=" * 60)
        print("WARNING: This tool permanently deletes users from the system!")
        print("Use only for incorrectly approved or mistakenly registered users.")
        print("")
        
        while True:
            print("\nChoose an option:")
            print("1. List all users")
            print("2. Search for user")
            print("3. Delete user by email")
            print("4. View recent deletion logs")
            print("5. Exit")
            
            choice = input("\nEnter choice (1-5): ").strip()
            
            if choice == "1":
                users = self.list_all_users()
                if users:
                    try:
                        user_num = int(input(f"\nEnter user number to delete (1-{len(users)}) or 0 to go back: "))
                        if user_num == 0:
                            continue
                        if 1 <= user_num <= len(users):
                            selected_user = users[user_num - 1]
                            self.delete_user_flow(selected_user[0], selected_user[1])
                        else:
                            print("❌ Invalid user number")
                    except ValueError:
                        print("❌ Please enter a valid number")
            
            elif choice == "2":
                search_term = input("Enter search term (email or name): ").strip()
                if search_term:
                    users = self.search_user(search_term)
                    if users:
                        try:
                            user_num = int(input(f"\nEnter user number to delete (1-{len(users)}) or 0 to go back: "))
                            if user_num == 0:
                                continue
                            if 1 <= user_num <= len(users):
                                selected_user = users[user_num - 1]
                                self.delete_user_flow(selected_user[0], selected_user[1])
                            else:
                                print("❌ Invalid user number")
                        except ValueError:
                            print("❌ Please enter a valid number")
            
            elif choice == "3":
                email = input("Enter user email to delete: ").strip()
                if email:
                    # Find user by email
                    users = self.search_user(email)
                    exact_match = [u for u in users if u[1].lower() == email.lower()]
                    if exact_match:
                        self.delete_user_flow(exact_match[0][0], exact_match[0][1])
                    else:
                        print(f"❌ No user found with email: {email}")
            
            elif choice == "4":
                self.show_deletion_logs()
            
            elif choice == "5":
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice. Please enter 1-5.")
    
    def delete_user_flow(self, user_id, user_email):
        """Complete flow for deleting a specific user"""
        # Show user details
        user_data = self.get_user_details(user_id)
        if not user_data:
            return
        
        # Get deletion confirmation
        deletion_reason = self.confirm_deletion(user_email)
        if not deletion_reason:
            return
        
        # Perform deletion
        print(f"\n🗑️ Processing deletion...")
        result = self.system.permanently_delete_user(
            user_id=user_id,
            deletion_reason=deletion_reason,
            performed_by_admin_id="admin",  # In real system, this would be the logged-in admin ID
            confirm_deletion=True
        )
        
        if result['success']:
            print(f"\n✅ SUCCESS: User {user_email} has been permanently deleted")
            print(f"   Deletion ID: {result['deletion_id']}")
            
            # Verify deletion
            verification = self.system.verify_user_completely_deleted(user_email)
            if verification:
                print("✅ Deletion verified - no traces remain in system")
            else:
                print("⚠️ Deletion may be incomplete - check manually")
        else:
            print(f"\n❌ FAILED: {result['error']}")
    
    def show_deletion_logs(self):
        """Show recent deletion logs"""
        logs = self.system.get_deletion_logs(days_back=30)
        
        if logs:
            print(f"\n📝 RECENT DELETION LOGS (Last 30 days)")
            print("=" * 80)
            print(f"{'Date':<12} {'Email':<30} {'Reason':<25} {'By Admin':<15}")
            print("-" * 80)
            
            for log in logs:
                deletion_id, user_id, deleted_at, deleted_by, reason, deletion_type, original_data = log
                import json
                original = json.loads(original_data)
                email = original['original_user_data']['email']
                date = deleted_at[:10]
                
                print(f"{date:<12} {email:<30} {reason[:24]:<25} {deleted_by:<15}")
        else:
            print("\n📝 No deletion logs found in the last 30 days")

def main():
    """Main function"""
    tool = AdminDeletionTool()
    tool.interactive_deletion()

if __name__ == "__main__":
    main()
