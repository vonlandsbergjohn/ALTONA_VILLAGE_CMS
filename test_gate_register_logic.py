#!/usr/bin/env python3

"""
Test the specific gate register issue
"""

import sys
import os

# Add the project directory to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'altona_village_cms', 'src'))

def test_gate_register_logic():
    """Test the gate register logic directly"""
    try:
        from models.user import User, Resident, Owner, Vehicle, db
        from main import app
        
        with app.app_context():
            print("=== Testing Gate Register Logic ===")
            
            # Get all active users
            active_users = User.query.filter_by(status='active').all()
            print(f"Found {len(active_users)} active users")
            
            gate_entries = []
            
            for user in active_users:
                # Skip admin users
                if user.role == 'admin':
                    print(f"Skipping admin user: {user.email}")
                    continue
                
                print(f"Processing user: {user.email}")
                print(f"  is_resident(): {user.is_resident()}")
                print(f"  is_owner(): {user.is_owner()}")
                print(f"  user.resident: {user.resident}")
                print(f"  user.owner: {user.owner}")
                
                # Determine resident status and get relevant data
                resident_data = None
                owner_data = None
                status = 'Unknown'
                
                if user.is_resident() and user.is_owner():
                    status = 'Owner-Resident'
                    resident_data = user.resident
                    owner_data = user.owner
                elif user.is_resident():
                    status = 'Resident'
                    resident_data = user.resident
                elif user.is_owner():
                    status = 'Non-Resident Owner'
                    owner_data = user.owner
                
                print(f"  Status: {status}")
                print(f"  Resident data: {resident_data}")
                print(f"  Owner data: {owner_data}")
                
                # Get primary data source (residents get priority for intercom codes)
                primary_data = resident_data if resident_data else owner_data
                
                if not primary_data:
                    print(f"  No primary data, skipping user")
                    continue  # Skip if no resident or owner data
                
                print(f"  Primary data: {primary_data.first_name} {primary_data.last_name}")
                
                # Get vehicle registrations for this user
                vehicle_registrations = []
                if resident_data:
                    vehicles = Vehicle.query.filter_by(resident_id=resident_data.id).all()
                    vehicle_registrations = [v.registration_number for v in vehicles]
                    print(f"  Found {len(vehicles)} resident vehicles: {vehicle_registrations}")
                elif owner_data:
                    # Owners also need vehicles for property visits
                    vehicles = Vehicle.query.filter_by(owner_id=owner_data.id).all()
                    vehicle_registrations = [v.registration_number for v in vehicles]
                    print(f"  Found {len(vehicles)} owner vehicles: {vehicle_registrations}")
                
                # Create entry for gate register
                entry = {
                    'resident_status': status,
                    'surname': primary_data.last_name or '',
                    'first_name': primary_data.first_name or '',
                    'street_number': primary_data.street_number or '',
                    'street_name': primary_data.street_name or '',
                    'vehicle_registrations': vehicle_registrations,
                    'erf_number': primary_data.erf_number or '',
                    'intercom_code': primary_data.intercom_code or '',
                    'sort_key': (primary_data.street_name or '').upper()
                }
                
                gate_entries.append(entry)
                print(f"  Added entry for {primary_data.first_name} {primary_data.last_name}")
                print("")
            
            # Sort by street name alphabetically
            gate_entries.sort(key=lambda x: x['sort_key'])
            
            print(f"=== Final Gate Register ===")
            print(f"Total entries: {len(gate_entries)}")
            for entry in gate_entries:
                vehicles_str = ', '.join(entry['vehicle_registrations']) if entry['vehicle_registrations'] else 'No vehicles'
                print(f"  {entry['resident_status']}: {entry['first_name']} {entry['surname']} - {entry['street_number']} {entry['street_name']} - {vehicles_str}")
            
            return {
                'success': True,
                'data': gate_entries,
                'total_entries': len(gate_entries)
            }
            
    except Exception as e:
        print(f"Error testing gate register: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    result = test_gate_register_logic()
    if result['success']:
        print("✅ Gate register logic test successful!")
    else:
        print(f"❌ Gate register logic test failed: {result['error']}")
