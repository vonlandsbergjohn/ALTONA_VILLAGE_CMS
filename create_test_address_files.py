#!/usr/bin/env python3
"""
Test the address mappings upload system with a sample dataset.
Creates a test CSV with 50 sample address mappings to verify large upload capability.
"""

import csv
import os

def create_test_address_file():
    """Create a test CSV file with sample address mappings"""
    
    print("🧪 Creating Test Address Mappings File")
    print("=" * 50)
    
    # Sample data with realistic ERF numbers and addresses
    test_data = []
    
    # Create 50 sample addresses
    streets = [
        ("Yellowwood", "Crescent"),
        ("Oak", "Street"),
        ("Pine", "Avenue"),
        ("Maple", "Drive"),
        ("Birch", "Lane"),
        ("Cedar", "Close"),
        ("Willow", "Road"),
        ("Elm", "Way"),
        ("Ash", "Court"),
        ("Poplar", "Gardens")
    ]
    
    base_erf = 30000
    for i in range(50):
        street_name, street_type = streets[i % len(streets)]
        street_number = (i % 30) + 1  # Street numbers 1-30
        erf_number = base_erf + i
        
        full_address = f"{street_number} {street_name} {street_type}, Altona Village, 6850"
        
        test_data.append({
            'erf_number': erf_number,
            'street_number': street_number,
            'street_name': f"{street_name} {street_type}",
            'suburb': 'Altona Village',
            'postal_code': '6850'
        })
    
    # Write to CSV file
    filename = "test_address_mappings_50_records.csv"
    filepath = os.path.join(os.getcwd(), filename)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['erf_number', 'street_number', 'street_name', 'suburb', 'postal_code']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in test_data:
            writer.writerow(row)
    
    file_size = os.path.getsize(filepath)
    
    print(f"✅ Created test file: {filename}")
    print(f"📊 Records: {len(test_data)}")
    print(f"📁 File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    print(f"📍 Location: {filepath}")
    
    print(f"\n🎯 Upload Test Instructions:")
    print(f"1. Go to Admin Dashboard → Address Mappings")
    print(f"2. Upload the file: {filename}")
    print(f"3. Verify all 50 records are imported successfully")
    print(f"4. Test the pagination (should show 50 records across pages)")
    
    # Show sample of data
    print(f"\n📋 Sample Data (first 5 records):")
    for i, record in enumerate(test_data[:5]):
        print(f"  ERF {record['erf_number']}: {record['street_number']} {record['street_name']}")
    
    return filepath

def create_large_test_file():
    """Create a larger test file with 300 records for stress testing"""
    
    print("\n🚀 Creating Large Test File (300 records)")
    print("=" * 50)
    
    test_data = []
    streets = [
        ("Yellowwood", "Crescent"), ("Oak", "Street"), ("Pine", "Avenue"),
        ("Maple", "Drive"), ("Birch", "Lane"), ("Cedar", "Close"),
        ("Willow", "Road"), ("Elm", "Way"), ("Ash", "Court"),
        ("Poplar", "Gardens"), ("Magnolia", "Street"), ("Cypress", "Avenue"),
        ("Fir", "Drive"), ("Spruce", "Lane"), ("Redwood", "Close")
    ]
    
    base_erf = 40000
    for i in range(300):
        street_name, street_type = streets[i % len(streets)]
        street_number = (i % 50) + 1  # Street numbers 1-50
        erf_number = base_erf + i
        
        full_address = f"{street_number} {street_name} {street_type}, Altona Village, 6850"
        
        test_data.append({
            'erf_number': erf_number,
            'street_number': street_number,
            'street_name': f"{street_name} {street_type}",
            'suburb': 'Altona Village',
            'postal_code': '6850'
        })
    
    # Write to CSV file
    filename = "test_address_mappings_300_records.csv"
    filepath = os.path.join(os.getcwd(), filename)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['erf_number', 'street_number', 'street_name', 'suburb', 'postal_code']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in test_data:
            writer.writerow(row)
    
    file_size = os.path.getsize(filepath)
    
    print(f"✅ Created large test file: {filename}")
    print(f"📊 Records: {len(test_data)}")
    print(f"📁 File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    print(f"📍 Location: {filepath}")
    
    print(f"\n⚡ Stress Test Instructions:")
    print(f"1. This file tests the 300+ record upload capability")
    print(f"2. Upload should take 30-60 seconds")
    print(f"3. Pagination will show 6 pages (50 records per page)")
    print(f"4. Test search functionality across all records")
    
    return filepath

if __name__ == "__main__":
    # Create both test files
    create_test_address_file()
    create_large_test_file()
    
    print(f"\n🎉 Test files created successfully!")
    print(f"   Ready to test large address mapping uploads!")
