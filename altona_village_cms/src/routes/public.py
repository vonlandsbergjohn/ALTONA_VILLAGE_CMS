from flask import Blueprint, jsonify
from src.models.user import ErfAddressMapping

# Public API blueprint for address lookups
public_bp = Blueprint('public', __name__)

@public_bp.route('/erf-lookup/<erf_number>', methods=['GET'])
def lookup_erf_address(erf_number):
    """Public endpoint to lookup address by ERF number"""
    try:
        address_data = ErfAddressMapping.get_address_by_erf(erf_number)
        
        if address_data:
            return jsonify({
                'success': True,
                'data': {
                    'erf_number': address_data['erf_number'],
                    'street_number': address_data['street_number'],
                    'street_name': address_data['street_name'],
                    'full_address': address_data['full_address'],
                    'suburb': address_data.get('suburb'),
                    'postal_code': address_data.get('postal_code')
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'No address found for ERF {erf_number}'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
