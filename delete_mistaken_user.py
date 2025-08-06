#!/usr/bin/env python3
"""
Delete the mistaken admin user
"""

from remove_mistaken_user import permanently_delete_user_by_email, verify_deletion

def main():
    # Delete the mistaken user
    email_to_delete = "vonlandsbergjohn@gmail.com"
    
    print(f"🗑️ REMOVING MISTAKEN USER: {email_to_delete}")
    print("=" * 60)
    
    success = permanently_delete_user_by_email(email_to_delete)
    
    if success:
        print(f"\n🔍 VERIFICATION:")
        verify_deletion(email_to_delete)
        
        print(f"\n✅ CLEANUP COMPLETE")
        print(f"   The mistaken user {email_to_delete} has been completely removed")
        print(f"   This was an admin account with no resident/owner data")
    else:
        print(f"\n❌ DELETION FAILED")

if __name__ == "__main__":
    main()
