#!/usr/bin/env python3

import sys
import os
sys.path.append('altona_village_cms/src')

from models.user import db, User, Resident, Owner, Vehicle
from main import app

def check_database():
    with app.app_context():
        print("=== USER STATUS VALUES ===")
        users = User.query.all()
        for user in users:
            print(f"User {user.id} ({user.username}): status='{user.status}', role='{user.role}'")
        
        print("\n=== RESIDENT STATUS VALUES ===")
        residents = Resident.query.all()
        for resident in residents:
            user = User.query.get(resident.user_id)
            print(f"Resident {resident.id} (user {resident.user_id}): status='{resident.status}', user_status='{user.status if user else 'N/A'}'")
        
        print("\n=== OWNER STATUS VALUES ===")
        owners = Owner.query.all()
        for owner in owners:
            user = User.query.get(owner.user_id)
            print(f"Owner {owner.id} (user {owner.user_id}): status='{owner.status}', user_status='{user.status if user else 'N/A'}'")
        
        print("\n=== ACTIVE USERS CHECK ===")
        active_users = User.query.filter_by(status='active').all()
        print(f"Users with status='active': {len(active_users)}")
        for user in active_users:
            print(f"  - {user.username} (role: {user.role})")

if __name__ == "__main__":
    check_database()
