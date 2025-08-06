#!/usr/bin/env python3

"""
Debug transition status update - check for specific error causing 500
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'altona_village_cms', 'src'))

from models.user import db, User, UserTransitionRequest, TransitionRequestUpdate
from routes.transition_requests import handle_user_termination
from flask import Flask
from datetime import datetime
import traceback

def debug_transition_status():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///altona_village_cms/src/database/app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    with app.app_context():
        db.init_app(app)
        
        try:
            # Find recent transition requests
            requests = UserTransitionRequest.query.filter_by(status='in_progress').limit(5).all()
            
            print(f"Found {len(requests)} in-progress transition requests:")
            for req in requests:
                print(f"- ID: {req.id}")
                print(f"  User ID: {req.user_id}")
                print(f"  ERF: {req.erf_number}")
                print(f"  Type: {req.new_occupant_type}")
                print(f"  Request Type: {req.request_type}")
                print()
                
                # Test the handle_user_termination function with this request
                if req.new_occupant_type == 'terminated':
                    print(f"Testing termination for request {req.id}...")
                    try:
                        result = handle_user_termination(req)
                        print(f"Termination result: {result}")
                    except Exception as e:
                        print(f"ERROR in handle_user_termination: {str(e)}")
                        print(f"Traceback: {traceback.format_exc()}")
                    print()
                    
        except Exception as e:
            print(f"Error: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    debug_transition_status()
