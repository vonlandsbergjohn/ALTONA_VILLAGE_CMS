#!/usr/bin/env python3
"""
Automated User Archive Scheduler
Automatically processes users for archival based on business rules
"""

from user_archive_deletion_system import UserArchiveDeletionSystem
from datetime import datetime, timedelta
import json
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('user_archive_log.txt'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ArchiveScheduler:
    def __init__(self):
        self.system = UserArchiveDeletionSystem()
        self.config = {
            'tenant_grace_period_days': 7,      # Grace period for tenants after moveout
            'owner_retention_years': 2,         # How long to keep owner data
            'auto_archive_enabled': True,       # Enable automatic archiving
            'require_manual_approval': False,   # Require manual approval for archiving
            'notification_email': None          # Admin email for notifications
        }
    
    def load_config(self, config_file='archive_config.json'):
        """Load configuration from file"""
        try:
            with open(config_file, 'r') as f:
                loaded_config = json.load(f)
                self.config.update(loaded_config)
            logger.info(f"Configuration loaded from {config_file}")
        except FileNotFoundError:
            logger.info(f"Config file {config_file} not found, using defaults")
            self.save_config(config_file)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
    
    def save_config(self, config_file='archive_config.json'):
        """Save current configuration to file"""
        try:
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Configuration saved to {config_file}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def process_automatic_archival(self):
        """Process users for automatic archival based on business rules"""
        logger.info("🚀 Starting automatic archive processing")
        
        if not self.config['auto_archive_enabled']:
            logger.info("ℹ️ Automatic archiving is disabled")
            return
        
        try:
            # Get inactive users
            inactive_users = self.system.get_inactive_users_analysis()
            
            if not inactive_users:
                logger.info("✅ No inactive users found requiring archive action")
                return
            
            processed_count = 0
            for user in inactive_users:
                if self._should_auto_archive(user):
                    success = self._archive_user_automated(user)
                    if success:
                        processed_count += 1
                else:
                    logger.info(f"⏳ User {user['email']} requires manual review")
            
            logger.info(f"📊 Archive processing complete. Processed {processed_count}/{len(inactive_users)} users")
            
            # Clean up old archives
            self._cleanup_old_archives()
            
        except Exception as e:
            logger.error(f"❌ Error during automatic archive processing: {e}")
    
    def _should_auto_archive(self, user_data):
        """Determine if a user should be automatically archived"""
        
        # Check if manual approval is required
        if self.config['require_manual_approval']:
            return False
        
        # Allow auto-archive for these scenarios
        auto_archive_actions = [
            'immediate_deletion',           # Tenants and sold property owners
            'archive_with_limited_retention'  # Former owners with property history only
        ]
        
        if user_data['recommended_action'] in auto_archive_actions:
            # Check grace periods
            if user_data['user_type'] == 'tenant_only':
                # Check if grace period has passed
                grace_period = timedelta(days=self.config['tenant_grace_period_days'])
                # Would need to check actual moveout date from database
                return True  # For now, allow immediate processing
            
            elif user_data['user_type'] == 'owner_only':
                # Check if enough time has passed since property transfer
                return True  # For now, allow immediate processing
            
            return True
        
        # Require manual review for complex cases
        return False
    
    def _archive_user_automated(self, user_data):
        """Archive a user automatically"""
        try:
            reason = f"Automated archive - {user_data['recommended_action']} - {datetime.now().isoformat()}"
            admin_id = "automated_scheduler"
            
            logger.info(f"🗄️ Auto-archiving user: {user_data['email']} ({user_data['user_type']})")
            
            success = self.system.archive_user(user_data['user_id'], reason, admin_id)
            
            if success:
                logger.info(f"✅ Successfully archived {user_data['email']}")
            else:
                logger.error(f"❌ Failed to archive {user_data['email']}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error archiving {user_data['email']}: {e}")
            return False
    
    def _cleanup_old_archives(self):
        """Clean up old archive records"""
        try:
            retention_days = self.config['owner_retention_years'] * 365
            deleted_count = self.system.cleanup_old_archives(retention_days)
            
            if deleted_count > 0:
                logger.info(f"🧹 Cleaned up {deleted_count} old archive records")
            
        except Exception as e:
            logger.error(f"❌ Error during archive cleanup: {e}")
    
    def generate_archive_report(self):
        """Generate a report of archive activities"""
        try:
            logger.info("📊 Generating archive report")
            
            # Get recent archives
            recent_archives = self.system.get_archived_users(days_since_archive=30)
            
            # Get inactive users awaiting action
            inactive_users = self.system.get_inactive_users_analysis()
            
            report = {
                'generated_at': datetime.now().isoformat(),
                'recent_archives_30_days': len(recent_archives),
                'pending_archive_actions': len(inactive_users),
                'recent_archives': [
                    {
                        'email': archive[7],
                        'user_type': archive[5],
                        'archived_date': archive[2],
                        'reason': archive[4]
                    }
                    for archive in recent_archives
                ],
                'pending_actions': [
                    {
                        'email': user['email'],
                        'user_type': user['user_type'],
                        'recommended_action': user['recommended_action'],
                        'can_auto_archive': self._should_auto_archive(user)
                    }
                    for user in inactive_users
                ]
            }
            
            # Save report
            report_file = f"archive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=4)
            
            logger.info(f"📄 Archive report saved to {report_file}")
            
            # Print summary
            print("\n📊 ARCHIVE SYSTEM REPORT")
            print("=" * 40)
            print(f"Recent archives (30 days): {report['recent_archives_30_days']}")
            print(f"Pending archive actions: {report['pending_archive_actions']}")
            
            if report['pending_actions']:
                print("\nPending Actions:")
                for action in report['pending_actions']:
                    auto_flag = "🤖" if action['can_auto_archive'] else "👤"
                    print(f"  {auto_flag} {action['email']} - {action['recommended_action']}")
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Error generating report: {e}")
            return None

def main():
    """Main scheduler function"""
    scheduler = ArchiveScheduler()
    
    print("🏠 ALTONA VILLAGE CMS - AUTOMATED ARCHIVE SCHEDULER")
    print("=" * 60)
    
    # Load configuration
    scheduler.load_config()
    
    print("\nSelect mode:")
    print("1. Run automatic archive processing")
    print("2. Generate archive report only")
    print("3. Configure settings")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        scheduler.process_automatic_archival()
        scheduler.generate_archive_report()
    elif choice == "2":
        scheduler.generate_archive_report()
    elif choice == "3":
        configure_settings(scheduler)
    elif choice == "4":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")

def configure_settings(scheduler):
    """Configure archive settings"""
    print("\n⚙️ ARCHIVE SETTINGS")
    print("-" * 30)
    
    print(f"Current settings:")
    for key, value in scheduler.config.items():
        print(f"  {key}: {value}")
    
    print(f"\nWhich setting would you like to change?")
    print("1. Auto archive enabled")
    print("2. Tenant grace period days")
    print("3. Owner retention years")
    print("4. Require manual approval")
    print("5. Save and exit")
    
    choice = input("Enter choice: ").strip()
    
    if choice == "1":
        enabled = input("Enable auto archive? (y/n): ").strip().lower() == 'y'
        scheduler.config['auto_archive_enabled'] = enabled
    elif choice == "2":
        days = input("Tenant grace period days: ").strip()
        if days.isdigit():
            scheduler.config['tenant_grace_period_days'] = int(days)
    elif choice == "3":
        years = input("Owner retention years: ").strip()
        if years.isdigit():
            scheduler.config['owner_retention_years'] = int(years)
    elif choice == "4":
        manual = input("Require manual approval? (y/n): ").strip().lower() == 'y'
        scheduler.config['require_manual_approval'] = manual
    elif choice == "5":
        scheduler.save_config()
        print("✅ Settings saved!")
        return
    
    # Recursive call to continue configuring
    configure_settings(scheduler)

if __name__ == "__main__":
    main()
