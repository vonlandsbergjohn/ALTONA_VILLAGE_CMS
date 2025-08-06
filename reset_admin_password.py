#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'altona_village_cms'))

from src.models.user import db, User
from src.main import app
from werkzeug.security import generate_password_hash

app_context = app.app_context()
app_context.push()

try:
    print("Resetting admin password...")
    
    # Find the admin user
    admin_user = User.query.filter_by(email='vonlandsbergjohn@gmail.com').first()
    
    if admin_user:
        # Set a new password
        new_password = 'admin123'
        admin_user.password_hash = generate_password_hash(new_password)
        
        # Commit the change
        db.session.commit()
        
        print(f"✅ Password reset successfully!")
        print(f"Login with: {admin_user.email} / {new_password}")
        
    else:
        print("❌ Admin user not found")
        
except Exception as e:
    print(f"❌ Error: {e}")
    db.session.rollback()
    
finally:
    app_context.pop()
