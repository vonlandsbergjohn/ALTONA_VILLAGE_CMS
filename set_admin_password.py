#!/usr/bin/env python3
"""
Set Admin Password for Testing
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'altona_village_cms', 'src'))

from models.user import User, db
from flask import Flask
from werkzeug.security import generate_password_hash

# Create minimal Flask app for database context
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///altona_village_cms/src/database/app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Fix the database path
import os
base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, 'altona_village_cms', 'src', 'database', 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

# Initialize database
db.init_app(app)

def set_admin_password():
    """Set admin password to a known value for testing"""
    with app.app_context():
        try:
            # Find admin user
            admin = User.query.filter_by(email='vonlandsbergjohn@gmail.com', role='admin').first()
            
            if not admin:
                print("❌ Admin user not found")
                return False
            
            # Set password to 'admin123'
            new_password = 'admin123'
            admin.password_hash = generate_password_hash(new_password)
            
            db.session.commit()
            
            print(f"✅ Admin password set to: {new_password}")
            print(f"Admin email: {admin.email}")
            return True
            
        except Exception as e:
            print(f"❌ Error setting admin password: {str(e)}")
            return False

if __name__ == "__main__":
    print("🔧 Setting Admin Password for Testing")
    set_admin_password()
