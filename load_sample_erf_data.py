#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'altona_village_cms', 'src'))

from main import app
from models.user import ErfAddressMapping, db
import csv

def load_sample_erf_data():
    """Load sample ERF mapping data into the database"""
    
    with app.app_context():
        print("=== Loading Sample ERF Data ===\n")
        
        # Check if data already exists
        existing_count = ErfAddressMapping.query.count()
        print(f"Current ERF mappings in database: {existing_count}")
        
        if existing_count > 0:
            print("Some ERF mappings already exist. Clearing existing data...")
            ErfAddressMapping.query.delete()
            db.session.commit()
        
        # Load data from CSV
        csv_file = "sample_erf_mappings.csv"
        if not os.path.exists(csv_file):
            print(f"❌ Sample file {csv_file} not found!")
            return
        
        print(f"Loading data from {csv_file}...")
        
        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            count = 0
            
            for row in reader:
                erf_number = row['erf_number'].strip()
                street_number = row['street_number'].strip()
                street_name = row['street_name'].strip()
                
                # Create mapping
                mapping = ErfAddressMapping(
                    erf_number=erf_number,
                    street_number=street_number,
                    street_name=street_name,
                    full_address=f"{street_number} {street_name}",
                    suburb="Altona Village",
                    postal_code="6850"
                )
                
                db.session.add(mapping)
                count += 1
                print(f"  Added ERF {erf_number}: {street_number} {street_name}")
        
        db.session.commit()
        print(f"\n✅ Successfully loaded {count} ERF mappings!")
        
        # Verify the data
        print(f"\nVerifying data...")
        total_mappings = ErfAddressMapping.query.count()
        print(f"Total ERF mappings in database: {total_mappings}")
        
        # Test a few lookups
        test_erfs = ['27727', '27728', '27800']
        for erf in test_erfs:
            mapping = ErfAddressMapping.query.filter_by(erf_number=erf).first()
            if mapping:
                print(f"  ERF {erf}: {mapping.full_address}")
            else:
                print(f"  ERF {erf}: Not found")

if __name__ == "__main__":
    load_sample_erf_data()
