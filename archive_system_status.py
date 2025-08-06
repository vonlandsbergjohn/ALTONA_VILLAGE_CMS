#!/usr/bin/env python3
"""
Archive System Status Summary
Quick overview of the archive system status
"""

from user_archive_deletion_system import UserArchiveDeletionSystem
import sqlite3
import os

def main():
    """Display current archive system status"""
    print("🏠 ALTONA VILLAGE CMS - ARCHIVE SYSTEM STATUS")
    print("=" * 60)
    
    db_path = os.path.join(os.path.dirname(__file__), 'altona_village_cms', 'src', 'database', 'app.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if archive table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_archives'")
    has_archive_table = cursor.fetchone() is not None
    
    print(f"📊 SYSTEM STATUS")
    print("-" * 30)
    print(f"Archive System: {'✅ Active' if has_archive_table else '❌ Not Initialized'}")
    
    if has_archive_table:
        # Count archives
        cursor.execute("SELECT COUNT(*) FROM user_archives")
        archive_count = cursor.fetchone()[0]
        print(f"Total Archives: {archive_count}")
        
        # Recent archives
        cursor.execute("SELECT COUNT(*) FROM user_archives WHERE archived_at > datetime('now', '-30 days')")
        recent_count = cursor.fetchone()[0]
        print(f"Recent Archives (30 days): {recent_count}")
    
    # Count users by status
    print(f"\n👥 USER STATUS OVERVIEW")
    print("-" * 30)
    
    cursor.execute("SELECT status, COUNT(*) FROM users GROUP BY status")
    user_statuses = cursor.fetchall()
    
    for status, count in user_statuses:
        print(f"{status}: {count} users")
    
    # Check for pending transitions
    cursor.execute("SELECT COUNT(*) FROM user_transition_requests WHERE status = 'completed' AND new_occupant_type = 'terminated'")
    terminated_transitions = cursor.fetchone()[0]
    
    if terminated_transitions > 0:
        print(f"\n⚠️ ATTENTION")
        print("-" * 15)
        print(f"Terminated transitions requiring archive review: {terminated_transitions}")
    
    # System recommendations
    print(f"\n🎯 RECOMMENDATIONS")
    print("-" * 20)
    
    if not has_archive_table:
        print("• Initialize archive system by running archive analysis")
    
    if terminated_transitions > 0:
        print("• Run archive analysis to process terminated users")
        print("• Consider automated scheduling for regular processing")
    
    # Show archive config if exists
    config_file = 'archive_config.json'
    if os.path.exists(config_file):
        print("• Archive scheduler configuration found")
    else:
        print("• Create archive scheduler configuration for automated processing")
    
    conn.close()

if __name__ == "__main__":
    main()
