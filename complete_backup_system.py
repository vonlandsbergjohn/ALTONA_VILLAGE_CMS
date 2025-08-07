#!/usr/bin/env python3
"""
Altona Village CMS - Complete Backup System
Creates comprehensive backups including database, code, and configuration
"""

import os
import sqlite3
import json
import shutil
import zipfile
import subprocess
from datetime import datetime
import sys

class AltonaVillageBackupSystem:
    def __init__(self, project_root=None):
        if project_root is None:
            self.project_root = os.path.dirname(__file__)
        else:
            self.project_root = project_root
        
        self.db_path = os.path.join(self.project_root, 'altona_village_cms', 'src', 'database', 'app.db')
        self.backup_dir = os.path.join(self.project_root, 'BACKUPS')
        
        # Create backup directory if it doesn't exist
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_complete_backup(self, backup_name=None):
        """Create a complete backup including database, code, and configuration"""
        
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"altona_village_complete_backup_{timestamp}"
        
        backup_folder = os.path.join(self.backup_dir, backup_name)
        os.makedirs(backup_folder, exist_ok=True)
        
        print(f"🏠 ALTONA VILLAGE CMS - COMPLETE BACKUP")
        print(f"=" * 50)
        print(f"Backup Name: {backup_name}")
        print(f"Backup Location: {backup_folder}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 1. Backup Database
            print(f"\n📊 BACKING UP DATABASE...")
            db_backup_success = self._backup_database(backup_folder)
            
            # 2. Backup Code (excluding git and temp files)
            print(f"\n💾 BACKING UP CODE...")
            code_backup_success = self._backup_code(backup_folder)
            
            # 3. Backup Configuration
            print(f"\n⚙️ BACKING UP CONFIGURATION...")
            config_backup_success = self._backup_configuration(backup_folder)
            
            # 4. Create restoration instructions
            print(f"\n📝 CREATING RESTORATION INSTRUCTIONS...")
            self._create_restoration_instructions(backup_folder)
            
            # 5. Create ZIP archive
            print(f"\n📦 CREATING ZIP ARCHIVE...")
            zip_path = self._create_zip_archive(backup_folder, backup_name)
            
            print(f"\n✅ BACKUP COMPLETED SUCCESSFULLY!")
            print(f"   📁 Folder: {backup_folder}")
            print(f"   📦 ZIP: {zip_path}")
            print(f"   📊 Database: {'✅' if db_backup_success else '❌'}")
            print(f"   💾 Code: {'✅' if code_backup_success else '❌'}")
            print(f"   ⚙️ Config: {'✅' if config_backup_success else '❌'}")
            
            return {
                'success': True,
                'backup_folder': backup_folder,
                'zip_path': zip_path,
                'database_backed_up': db_backup_success,
                'code_backed_up': code_backup_success,
                'config_backed_up': config_backup_success
            }
            
        except Exception as e:
            print(f"\n❌ BACKUP FAILED: {e}")
            return {'success': False, 'error': str(e)}
    
    def _backup_database(self, backup_folder):
        """Backup database with full schema and data"""
        try:
            if not os.path.exists(self.db_path):
                print(f"   ⚠️ Database not found at: {self.db_path}")
                return False
            
            db_backup_folder = os.path.join(backup_folder, 'database')
            os.makedirs(db_backup_folder, exist_ok=True)
            
            # 1. Copy the actual database file
            db_backup_path = os.path.join(db_backup_folder, 'app.db')
            shutil.copy2(self.db_path, db_backup_path)
            print(f"   ✅ Database file copied to: app.db")
            
            # 2. Create SQL dump for portability
            sql_dump_path = os.path.join(db_backup_folder, 'database_dump.sql')
            self._create_sql_dump(sql_dump_path)
            print(f"   ✅ SQL dump created: database_dump.sql")
            
            # 3. Create JSON export of all data
            json_backup_path = os.path.join(db_backup_folder, 'database_export.json')
            self._export_database_to_json(json_backup_path)
            print(f"   ✅ JSON export created: database_export.json")
            
            # 4. Create database summary
            summary_path = os.path.join(db_backup_folder, 'database_summary.txt')
            self._create_database_summary(summary_path)
            print(f"   ✅ Database summary created: database_summary.txt")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Database backup failed: {e}")
            return False
    
    def _create_sql_dump(self, output_path):
        """Create a SQL dump of the database"""
        conn = sqlite3.connect(self.db_path)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"-- Altona Village CMS Database Dump\\n")
            f.write(f"-- Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"-- Database: {self.db_path}\\n\\n")
            
            # Dump schema and data
            for line in conn.iterdump():
                f.write(f"{line}\\n")
        
        conn.close()
    
    def _export_database_to_json(self, output_path):
        """Export all database tables to JSON format"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        database_export = {
            'export_date': datetime.now().isoformat(),
            'database_path': self.db_path,
            'tables': {}
        }
        
        for table in tables:
            try:
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                
                # Get column names
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [column[1] for column in cursor.fetchall()]
                
                # Convert rows to dictionaries
                table_data = []
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    table_data.append(row_dict)
                
                database_export['tables'][table] = {
                    'columns': columns,
                    'row_count': len(table_data),
                    'data': table_data
                }
                
            except Exception as e:
                database_export['tables'][table] = {
                    'error': str(e)
                }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(database_export, f, indent=2, default=str, ensure_ascii=False)
        
        conn.close()
    
    def _create_database_summary(self, output_path):
        """Create a human-readable database summary"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"ALTONA VILLAGE CMS - DATABASE SUMMARY\\n")
            f.write(f"=" * 50 + "\\n")
            f.write(f"Backup Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"Database Path: {self.db_path}\\n\\n")
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row[0] for row in cursor.fetchall()]
            
            f.write(f"TABLES SUMMARY:\\n")
            f.write(f"-" * 30 + "\\n")
            
            for table in tables:
                try:
                    # Get row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    row_count = cursor.fetchone()[0]
                    
                    # Get column info
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = cursor.fetchall()
                    
                    f.write(f"\\n📊 Table: {table}\\n")
                    f.write(f"   Rows: {row_count}\\n")
                    f.write(f"   Columns: {len(columns)}\\n")
                    for col in columns:
                        f.write(f"     - {col[1]} ({col[2]})\\n")
                    
                except Exception as e:
                    f.write(f"\\n❌ Table: {table} - Error: {e}\\n")
        
        conn.close()
    
    def _backup_code(self, backup_folder):
        """Backup all code files (excluding git, node_modules, etc.)"""
        try:
            code_backup_folder = os.path.join(backup_folder, 'code')
            
            # Files and folders to exclude
            exclude_patterns = {
                '.git', '.venv', 'venv', 'env', '__pycache__', 
                'node_modules', '.next', 'dist', 'build',
                '.DS_Store', 'Thumbs.db', '*.pyc', '*.pyo',
                'BACKUPS', '.env', '*.log'
            }
            
            def should_exclude(path):
                name = os.path.basename(path)
                return any(pattern in name or name.startswith(pattern.replace('*', '')) 
                          for pattern in exclude_patterns)
            
            # Copy project files
            for root, dirs, files in os.walk(self.project_root):
                # Skip excluded directories
                dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]
                
                # Calculate relative path
                rel_path = os.path.relpath(root, self.project_root)
                if rel_path == '.':
                    rel_path = ''
                
                # Skip if this directory should be excluded
                if should_exclude(root):
                    continue
                
                # Create directory structure
                dest_dir = os.path.join(code_backup_folder, rel_path)
                os.makedirs(dest_dir, exist_ok=True)
                
                # Copy files
                for file in files:
                    if not should_exclude(os.path.join(root, file)):
                        src_file = os.path.join(root, file)
                        dest_file = os.path.join(dest_dir, file)
                        try:
                            shutil.copy2(src_file, dest_file)
                        except Exception as e:
                            print(f"   ⚠️ Could not copy {file}: {e}")
            
            print(f"   ✅ Code files backed up to: code/")
            return True
            
        except Exception as e:
            print(f"   ❌ Code backup failed: {e}")
            return False
    
    def _backup_configuration(self, backup_folder):
        """Backup configuration and setup information"""
        try:
            config_backup_folder = os.path.join(backup_folder, 'configuration')
            os.makedirs(config_backup_folder, exist_ok=True)
            
            # Create environment setup information
            setup_info_path = os.path.join(config_backup_folder, 'setup_information.txt')
            with open(setup_info_path, 'w', encoding='utf-8') as f:
                f.write(f"ALTONA VILLAGE CMS - SETUP INFORMATION\\n")
                f.write(f"=" * 50 + "\\n")
                f.write(f"Backup Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n")
                
                f.write(f"PYTHON ENVIRONMENT:\\n")
                f.write(f"-" * 20 + "\\n")
                f.write(f"Python Version: {sys.version}\\n")
                f.write(f"Python Executable: {sys.executable}\\n\\n")
                
                # Try to get pip freeze output
                try:
                    result = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], 
                                          capture_output=True, text=True, cwd=self.project_root)
                    f.write(f"INSTALLED PACKAGES:\\n")
                    f.write(f"-" * 20 + "\\n")
                    f.write(result.stdout)
                except Exception as e:
                    f.write(f"Could not get pip freeze: {e}\\n")
                
                f.write(f"\\nPROJECT STRUCTURE:\\n")
                f.write(f"-" * 20 + "\\n")
                for root, dirs, files in os.walk(self.project_root):
                    # Skip deep and excluded directories
                    level = root.replace(self.project_root, '').count(os.sep)
                    if level > 3 or any(ex in root for ex in ['.git', '.venv', 'node_modules', '__pycache__']):
                        continue
                    
                    indent = ' ' * 2 * level
                    f.write(f"{indent}{os.path.basename(root)}/\\n")
                    
                    subindent = ' ' * 2 * (level + 1)
                    for file in files[:5]:  # Only show first 5 files
                        f.write(f"{subindent}{file}\\n")
                    if len(files) > 5:
                        f.write(f"{subindent}... and {len(files) - 5} more files\\n")
            
            # Copy important configuration files if they exist
            config_files = [
                'requirements.txt',
                'package.json',
                'README.md',
                '.gitignore',
                'deployment_guide.md'
            ]
            
            for config_file in config_files:
                src_path = os.path.join(self.project_root, config_file)
                if os.path.exists(src_path):
                    dest_path = os.path.join(config_backup_folder, config_file)
                    shutil.copy2(src_path, dest_path)
                    print(f"   ✅ Copied {config_file}")
            
            print(f"   ✅ Configuration backed up to: configuration/")
            return True
            
        except Exception as e:
            print(f"   ❌ Configuration backup failed: {e}")
            return False
    
    def _create_restoration_instructions(self, backup_folder):
        """Create detailed instructions for restoring from this backup"""
        instructions_path = os.path.join(backup_folder, 'RESTORATION_INSTRUCTIONS.md')
        
        with open(instructions_path, 'w', encoding='utf-8') as f:
            f.write("""# ALTONA VILLAGE CMS - RESTORATION INSTRUCTIONS

## Overview
This backup contains a complete snapshot of your Altona Village CMS system including:
- ✅ **Database** (SQLite with all resident data, vehicles, complaints, etc.)
- ✅ **Source Code** (Python backend, React frontend)
- ✅ **Configuration** (dependencies, settings)

## Quick Restoration Steps

### 1. 📁 Extract Backup
```bash
# Extract the ZIP file to your desired location
# Example: C:\\Projects\\Altona_Village_CMS_Restored
```

### 2. 📊 Restore Database
```bash
# Copy the database file back to the correct location
copy "database\\app.db" "altona_village_cms\\src\\database\\app.db"

# OR restore from SQL dump if needed:
# sqlite3 altona_village_cms/src/database/app.db < database/database_dump.sql
```

### 3. 🐍 Setup Python Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\\Scripts\\activate
# Mac/Linux:
source .venv/bin/activate

# Install dependencies (check configuration/requirements.txt)
pip install flask flask-cors flask-jwt-extended flask-sqlalchemy python-dotenv
```

### 4. 📦 Setup Frontend (if using React)
```bash
# Navigate to frontend directory
cd altona-village-frontend

# Install dependencies
npm install

# Build frontend
npm run build
```

### 5. ▶️ Start the System
```bash
# Start backend (from project root)
python altona_village_cms/src/main.py

# Start frontend (in separate terminal)
cd altona-village-frontend
npm run dev
```

### 6. ✅ Verify Restoration
- Open http://localhost:5173 (frontend)
- Login with your admin credentials
- Check that all data is present:
  - Users and residents
  - Vehicle registrations
  - Property information
  - Complaints and updates

## Alternative Restoration Methods

### From SQL Dump
If you need to restore to a different database system:
```bash
# Create new database and import
sqlite3 new_database.db < database/database_dump.sql
```

### From JSON Export
The `database/database_export.json` file contains all data in JSON format for manual import or migration to other systems.

## Troubleshooting

### Database Issues
- Check that `app.db` is in the correct location: `altona_village_cms/src/database/`
- Verify file permissions (database file should be writable)
- Check database integrity: `sqlite3 app.db "PRAGMA integrity_check;"`

### Missing Dependencies
- Check `configuration/setup_information.txt` for exact package versions
- Refer to `configuration/requirements.txt` for Python packages
- Refer to `configuration/package.json` for Node.js packages

### Port Conflicts
- Backend default: http://localhost:5000
- Frontend default: http://localhost:5173
- Change ports in configuration if needed

## Security Notes
⚠️ **This backup contains sensitive resident data!**
- Store backups securely
- Limit access to authorized personnel only
- Consider encryption for offsite storage
- Never commit database files to version control

## Support
For restoration assistance, check:
1. This restoration guide
2. Project README.md
3. Configuration files in the backup

---
**Backup Created:** {backup_date}
**System:** Altona Village Community Management System
""".format(backup_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        print(f"   ✅ Restoration instructions created: RESTORATION_INSTRUCTIONS.md")
    
    def _create_zip_archive(self, backup_folder, backup_name):
        """Create a ZIP archive of the backup"""
        zip_path = os.path.join(self.backup_dir, f"{backup_name}.zip")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(backup_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_path = os.path.relpath(file_path, backup_folder)
                    zipf.write(file_path, arc_path)
        
        print(f"   ✅ ZIP archive created: {backup_name}.zip")
        return zip_path
    
    def list_backups(self):
        """List all available backups"""
        print(f"🏠 ALTONA VILLAGE CMS - AVAILABLE BACKUPS")
        print(f"=" * 50)
        
        if not os.path.exists(self.backup_dir):
            print("No backups found.")
            return []
        
        backups = []
        for item in os.listdir(self.backup_dir):
            item_path = os.path.join(self.backup_dir, item)
            if os.path.isdir(item_path) or item.endswith('.zip'):
                stat = os.stat(item_path)
                backups.append({
                    'name': item,
                    'path': item_path,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'type': 'ZIP' if item.endswith('.zip') else 'Folder'
                })
        
        backups.sort(key=lambda x: x['modified'], reverse=True)
        
        for i, backup in enumerate(backups, 1):
            size_mb = backup['size'] / (1024 * 1024)
            print(f"{i}. {backup['name']}")
            print(f"   📦 Type: {backup['type']}")
            print(f"   📅 Date: {backup['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   📏 Size: {size_mb:.1f} MB")
            print()
        
        return backups

def main():
    """Main function for manual backup execution"""
    backup_system = AltonaVillageBackupSystem()
    
    print("Select an option:")
    print("1. Create complete backup")
    print("2. List existing backups")
    print("3. Create backup with custom name")
    
    choice = input("\\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        result = backup_system.create_complete_backup()
        if result['success']:
            print("\\n🎉 Backup completed successfully!")
        else:
            print(f"\\n❌ Backup failed: {result.get('error', 'Unknown error')}")
    
    elif choice == '2':
        backup_system.list_backups()
    
    elif choice == '3':
        custom_name = input("Enter backup name: ").strip()
        if custom_name:
            result = backup_system.create_complete_backup(custom_name)
            if result['success']:
                print("\\n🎉 Backup completed successfully!")
            else:
                print(f"\\n❌ Backup failed: {result.get('error', 'Unknown error')}")
        else:
            print("❌ Invalid backup name")
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
