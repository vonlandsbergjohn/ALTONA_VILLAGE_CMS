import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from src.models.user import db
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.admin import admin_bp
from src.routes.communication import communication_bp
from src.routes.resident import resident_bp
from src.routes.gate_register import gate_register_bp
from src.routes.admin_notifications import admin_notifications
from src.routes.transition_requests import transition_bp
from src.routes.public import public_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-string-change-in-production')

# Enable CORS for all routes
CORS(app)

# Initialize JWT
jwt = JWTManager(app)

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(resident_bp, url_prefix='/api/resident')
app.register_blueprint(communication_bp, url_prefix='/api/communication')
app.register_blueprint(gate_register_bp, url_prefix='/api/admin')
app.register_blueprint(admin_notifications, url_prefix='/api')
app.register_blueprint(transition_bp, url_prefix='/api/transition')
app.register_blueprint(public_bp, url_prefix='/api/public')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create tables and default admin user
with app.app_context():
    db.create_all()
    
    # Create default admin user if it doesn't exist
    from src.models.user import User
    admin_user = User.query.filter_by(email='vonlandsbergjohn@gmail.com').first()
    if not admin_user:
        admin_user = User(
            email='vonlandsbergjohn@gmail.com',
            role='admin',
            status='active'
        )
        # Use environment variable for admin password in production
        admin_password = os.environ.get('ADMIN_PASSWORD', 'dGdFHLCJxx44ykq')
        admin_user.set_password(admin_password)
        db.session.add(admin_user)
        db.session.commit()
        print(f"Default admin user created: vonlandsbergjohn@gmail.com")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)
