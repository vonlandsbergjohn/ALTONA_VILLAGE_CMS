# Backend Integration for Interactive Map

from flask import Blueprint, jsonify, request
from models.user import Property, Resident, Owner
from utils.auth import token_required

# Create a new blueprint for map-related endpoints
map_bp = Blueprint('map', __name__)

@map_bp.route('/api/map/properties', methods=['GET'])
def get_map_properties():
    """
    Get all properties with their coordinates for the interactive map
    This endpoint provides property data in the format expected by the frontend map component
    """
    try:
        # Get search term if provided
        search_term = request.args.get('search', '').lower()
        
        # Query all properties from database
        properties_query = Property.query
        
        # Apply search filter if provided
        if search_term:
            properties_query = properties_query.filter(
                Property.erf_number.ilike(f'%{search_term}%') |
                Property.address.ilike(f'%{search_term}%') |
                Property.street_name.ilike(f'%{search_term}%')
            )
        
        properties = properties_query.all()
        
        # Format properties for the map component
        map_properties = []
        for prop in properties:
            # You'll need to add coordinate fields to your Property model
            # or store them in a separate mapping table
            
            property_data = {
                'erf': prop.erf_number,
                'street': prop.address,
                'streetNumber': prop.street_number or '',
                'streetName': prop.street_name or '',
                'coordinates': {
                    # These coordinates should be stored in your database
                    # For now, they return None - you'll need to populate these
                    'x': getattr(prop, 'map_x_coordinate', None),
                    'y': getattr(prop, 'map_y_coordinate', None)
                },
                'section': getattr(prop, 'section', 'Unknown'),
                'notes': '',
                'status': 'available'  # You can determine this based on resident/owner presence
            }
            
            # Determine property status
            if prop.resident_id or prop.owner_id:
                property_data['status'] = 'occupied'
            
            # Only include properties that have coordinates
            if property_data['coordinates']['x'] is not None and property_data['coordinates']['y'] is not None:
                map_properties.append(property_data)
        
        return jsonify({
            'success': True,
            'properties': map_properties,
            'total': len(map_properties)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch map properties: {str(e)}'
        }), 500

@map_bp.route('/api/map/property/<erf_number>', methods=['GET'])
def get_property_details(erf_number):
    """
    Get detailed information about a specific property
    """
    try:
        property_obj = Property.query.filter_by(erf_number=erf_number).first()
        
        if not property_obj:
            return jsonify({
                'success': False,
                'error': 'Property not found'
            }), 404
        
        # Get resident/owner information if available
        resident_info = None
        owner_info = None
        
        if property_obj.resident:
            resident_info = {
                'name': f"{property_obj.resident.first_name} {property_obj.resident.last_name}",
                'phone': property_obj.resident.phone_number
            }
        
        if property_obj.owner:
            owner_info = {
                'name': f"{property_obj.owner.first_name} {property_obj.owner.last_name}",
                'phone': property_obj.owner.phone_number
            }
        
        property_details = {
            'erf': property_obj.erf_number,
            'address': property_obj.address,
            'street_number': property_obj.street_number,
            'street_name': property_obj.street_name,
            'coordinates': {
                'x': getattr(property_obj, 'map_x_coordinate', None),
                'y': getattr(property_obj, 'map_y_coordinate', None)
            },
            'resident': resident_info,
            'owner': owner_info,
            'status': 'occupied' if (property_obj.resident_id or property_obj.owner_id) else 'available'
        }
        
        return jsonify({
            'success': True,
            'property': property_details
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch property details: {str(e)}'
        }), 500

# Database migration to add coordinate fields to Property model
"""
To use this backend integration, you'll need to add coordinate fields to your Property model:

In models/user.py, add these fields to the Property class:

    # Map coordinates (percentage values 0-100)
    map_x_coordinate = db.Column(db.Float)  # X position as percentage from left
    map_y_coordinate = db.Column(db.Float)  # Y position as percentage from top
    section = db.Column(db.String(100))     # Property section/area grouping

Then create a migration script:
"""

def create_coordinate_migration():
    """
    Migration script to add coordinate fields to existing Property table
    Run this once to update your database schema
    """
    from models.user import db
    
    try:
        # Add coordinate columns
        db.engine.execute("""
            ALTER TABLE properties 
            ADD COLUMN map_x_coordinate FLOAT,
            ADD COLUMN map_y_coordinate FLOAT,
            ADD COLUMN section VARCHAR(100)
        """)
        
        print("✅ Successfully added coordinate fields to properties table")
        
        # You can populate coordinates here if you have the data
        # Example:
        """
        coordinate_data = [
            ('5555', 20.0, 30.0, 'North Section'),
            ('8888', 35.0, 25.0, 'Central Section'),
            ('4562', 50.0, 40.0, 'East Section'),
            # Add your property coordinates here
        ]
        
        for erf, x, y, section in coordinate_data:
            db.engine.execute(
                "UPDATE properties SET map_x_coordinate = ?, map_y_coordinate = ?, section = ? WHERE erf_number = ?",
                (x, y, section, erf)
            )
        """
        
        db.session.commit()
        print("✅ Migration completed successfully")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        db.session.rollback()

# Usage in main.py:
"""
# Add this to your main.py imports
from routes.map import map_bp

# Register the blueprint
app.register_blueprint(map_bp)

# Run migration (only once)
# create_coordinate_migration()
"""
