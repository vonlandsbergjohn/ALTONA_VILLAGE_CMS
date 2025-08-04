#!/usr/bin/env python3
"""
Test Gate Register Population After Transition
Check what happens to new users created via transition linking
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'altona_village_cms', 'src'))

# Initialize the Flask app environment
os.chdir(os.path.join(os.path.dirname(__file__), 'altona_village_cms', 'src'))
import main  # This will initialize the app and database
from models.user import db, User, Resident, Owner, Vehicle, UserTransitionRequest

def test_gate_register_erf_27727():
    """Check what's in the database for ERF 27727 after transition"""
    
    # Get the app context
    with main.app.app_context():
        print("🔍 DEBUGGING GATE REGISTER FOR ERF 27727")
        print("=" * 60)
    
    
        # 1. Check all users (regardless of status)
        print("\n1. ALL USERS IN DATABASE:")
        all_users = User.query.all()
        for user in all_users:
            print(f"   User ID: {user.id}, Email: {user.email}, Role: {user.role}, Status: {user.status}")
        
        # 2. Check active users only
        print("\n2. ACTIVE USERS ONLY:")
        active_users = User.query.filter_by(status='active').all()
        for user in active_users:
            print(f"   User ID: {user.id}, Email: {user.email}, Role: {user.role}")
        
        # 3. Check residents for ERF 27727
        print("\n3. RESIDENTS FOR ERF 27727:")
        residents_27727 = Resident.query.filter_by(erf_number='27727').all()
        for resident in residents_27727:
            print(f"   Resident ID: {resident.id}, User ID: {resident.user_id}, Name: {resident.first_name} {resident.last_name}")
            print(f"   Status: {resident.status}, ERF: {resident.erf_number}")
            
            # Check if this resident's user is active
            user = User.query.get(resident.user_id)
            if user:
                print(f"   Associated User Status: {user.status}, Role: {user.role}")
            else:
                print(f"   ⚠️  NO ASSOCIATED USER FOUND!")
        
        # 4. Check owners for ERF 27727
        print("\n4. OWNERS FOR ERF 27727:")
        owners_27727 = Owner.query.filter_by(erf_number='27727').all()
        for owner in owners_27727:
            print(f"   Owner ID: {owner.id}, User ID: {owner.user_id}, Name: {owner.first_name} {owner.last_name}")
            print(f"   Status: {owner.status}, ERF: {owner.erf_number}")
            
            # Check if this owner's user is active
            user = User.query.get(owner.user_id)
            if user:
                print(f"   Associated User Status: {user.status}, Role: {user.role}")
            else:
                print(f"   ⚠️  NO ASSOCIATED USER FOUND!")
        
        # 5. Simulate gate register logic for ERF 27727
        print("\n5. GATE REGISTER SIMULATION FOR ERF 27727:")
        active_users = User.query.filter_by(status='active').all()
        found_entries = []
        
        for user in active_users:
            if user.role == 'admin':
                continue
                
            # Check if this user has records for ERF 27727
            resident_data = None
            owner_data = None
            
            if user.resident and user.resident.erf_number == '27727' and user.resident.status == 'active':
                resident_data = user.resident
            if user.owner and user.owner.erf_number == '27727' and user.owner.status == 'active':
                owner_data = user.owner
            
            if resident_data or owner_data:
                primary_data = resident_data if resident_data else owner_data
                print(f"   ✅ FOUND: {primary_data.first_name} {primary_data.last_name} (ERF {primary_data.erf_number})")
                print(f"      User Status: {user.status}, Role: {user.role}")
                print(f"      Resident Status: {resident_data.status if resident_data else 'N/A'}")
                print(f"      Owner Status: {owner_data.status if owner_data else 'N/A'}")
                found_entries.append(user)
        
        if not found_entries:
            print("   ❌ NO GATE REGISTER ENTRIES FOUND FOR ERF 27727")
        
        # 6. Check the latest transition request for ERF 27727
        print("\n6. LATEST TRANSITION REQUEST FOR ERF 27727:")
        latest_transition = UserTransitionRequest.query.filter_by(erf_number='27727').order_by(UserTransitionRequest.created_at.desc()).first()
        if latest_transition:
            print(f"   Request ID: {latest_transition.id}")
            print(f"   Status: {latest_transition.status}")
            print(f"   Migration Completed: {latest_transition.migration_completed}")
            print(f"   New User ID: {latest_transition.new_user_id}")
            print(f"   New Occupant: {latest_transition.new_occupant_first_name} {latest_transition.new_occupant_last_name}")
            print(f"   New Occupant Type: {latest_transition.new_occupant_type}")
            
            # Check if the new user was actually created
            if latest_transition.new_user_id:
                new_user = User.query.get(latest_transition.new_user_id)
                if new_user:
                    print(f"   ✅ New User Created: {new_user.email} (Status: {new_user.status}, Role: {new_user.role})")
                    
                    # Check if this new user has resident/owner records
                    if new_user.resident:
                        print(f"   ✅ Has Resident Record: ERF {new_user.resident.erf_number}, Status: {new_user.resident.status}")
                    if new_user.owner:
                        print(f"   ✅ Has Owner Record: ERF {new_user.owner.erf_number}, Status: {new_user.owner.status}")
                else:
                    print(f"   ❌ NEW USER ID {latest_transition.new_user_id} NOT FOUND!")
        else:
            print("   ❌ NO TRANSITION REQUESTS FOUND FOR ERF 27727")

if __name__ == "__main__":
    test_gate_register_erf_27727()
