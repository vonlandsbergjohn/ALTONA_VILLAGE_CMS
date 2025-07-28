#!/usr/bin/env python3
"""
Test gate register API directly
"""
import sys
import os
sys.path.append('altona_village_cms/src')

from main import app
from models.user import User, Resident, Owner, Vehicle
import json

def test_gate_register():
    with app.app_context():
        print("=== TESTING GATE REGISTER DATA ===")
        
        # Get all active users
        active_users = User.query.filter_by(status='active').all()
        print(f"Found {len(active_users)} active users")
        
        gate_entries = []
        
        for user in active_users:
            if user.role == 'admin':
                print(f"Skipping admin user: {user.email}")
                continue
            
            print(f"\nProcessing user: {user.email}")
            print(f"  is_resident(): {user.is_resident()}")
            print(f"  is_owner(): {user.is_owner()}")
            print(f"  has resident record: {user.resident is not None}")
            print(f"  has owner record: {user.owner is not None}")
            
            # Determine resident status and get relevant data
            resident_data = None
            owner_data = None
            status = 'Unknown'
            
            if user.is_resident() and user.is_owner():
                status = 'Owner-Resident'
                resident_data = user.resident
                owner_data = user.owner
                print(f"  Status: {status}")
            elif user.is_resident():
                status = 'Resident'
                resident_data = user.resident
                print(f"  Status: {status}")
            elif user.is_owner():
                status = 'Non-Resident Owner'
                owner_data = user.owner
                print(f"  Status: {status}")
            
            # Get primary data source
            primary_data = resident_data if resident_data else owner_data
            
            if not primary_data:
                print(f"  No resident or owner data found - SKIPPING")
                continue
            
            print(f"  Primary data: {'resident' if resident_data else 'owner'}")
            print(f"  Name: {primary_data.first_name} {primary_data.last_name}")
            print(f"  Address: {primary_data.full_address}")
            
            # Get vehicles
            vehicle_registrations = []
            if resident_data:
                vehicles = Vehicle.query.filter_by(resident_id=resident_data.id).all()
                vehicle_registrations = [v.registration_number for v in vehicles]
                print(f"  Resident vehicles: {vehicle_registrations}")
            elif owner_data:
                vehicles = Vehicle.query.filter_by(owner_id=owner_data.id).all()
                vehicle_registrations = [v.registration_number for v in vehicles]
                print(f"  Owner vehicles: {vehicle_registrations}")
            
            # Create entry
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
            print(f"  Entry created successfully")
        
        print(f"\n=== FINAL RESULTS ===")
        print(f"Total gate entries: {len(gate_entries)}")
        
        if gate_entries:
            print("Sample entries:")
            for entry in gate_entries[:3]:  # Show first 3
                print(f"  - {entry['first_name']} {entry['surname']}: {entry['resident_status']}")
        
        return gate_entries

if __name__ == "__main__":
    test_gate_register()
