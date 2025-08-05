#!/usr/bin/env python3
"""
Script to create database tables for ERF address mappings
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from altona_village_cms.src.main import app
from altona_village_cms.src.models.user import db

def create_tables():
    """Create all database tables"""
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            print("📍 ERF Address Mapping table is ready for use")
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            return False
    return True

if __name__ == '__main__':
    create_tables()
