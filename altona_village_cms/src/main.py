import os
import sys

# Keep your original path setup
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# Import the db only (avoid importing routes/blueprints here)
from src.models.user import db


def create_app() -> Flask:
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

    # Secrets
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-string-change-in-production')

    # Uploads
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
    upload_dir = os.path.join(os.path.dirname(__file__), 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_dir

    # Database: prefer DATABASE_URL (Render Postgres) else fall back to SQLite
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    else:
        db_dir = os.path.join(os.path.dirname(__file__), 'database')
        os.makedirs(db_dir, exist_ok=True)
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(db_dir, 'app.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Extensions
    CORS(app)
    JWTManager(app)
    db.init_app(app)

    with app.app_context():
        # Ensure models are loaded before create_all
        from src.models import user as _models  # noqa: F401

        db.create_all()

        # Register blueprints with lazy imports to avoid import-time side effects
        from src.routes.user import user_bp
        from src.routes.auth import auth_bp
        from src.routes.admin import admin_bp
        from src.routes.communication import communication_bp
        from src.routes.resident import resident_bp
        from src.routes.gate_register import gate_register_bp
        from src.routes.public import public_bp
        from src.routes.user_management import user_management_bp
        from src.routes.transition_requests import transition_bp
        from src.routes.transition_linking import transition_linking_bp

        app.register_blueprint(user_bp, url_prefix='/api')
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(admin_bp, url_prefix='/api/admin')
        app.register_blueprint(resident_bp, url_prefix='/api/resident')
        app.register_blueprint(communication_bp, url_prefix='/api/communication')
        app.register_blueprint(gate_register_bp, url_prefix='/api/admin')
        app.register_blueprint(public_bp, url_prefix='/api/public')
        app.register_blueprint(user_management_bp, url_prefix='/api')
        app.register_blueprint(transition_bp, url_prefix='/api/transition')
        app.register_blueprint(transition_linking_bp)

        # admin_notifications was previously causing an import-time DB open.
        # We import/register it last with a guard so it can’t crash the whole app.
        try:
            from src.routes.admin_notifications import admin_notifications
            app.register_blueprint(admin_notifications, url_prefix='/api')
        except Exception as e:
            app.logger.error(f"admin_notifications failed to register: {e}")

        # Ensure a default admin user exists
        from src.models.user import User
        admin_email = 'vonlandsbergjohn@gmail.com'
        admin_user = User.query.filter_by(email=admin_email).first()
        if not admin_user:
            admin_user = User(email=admin_email, role='admin', status='active')
            admin_password = os.environ.get('ADMIN_PASSWORD', 'dGdFHLCJxx44ykq')
            admin_user.set_password(admin_password)
            db.session.add(admin_user)
            db.session.commit()
            print(f"Default admin user created: {admin_email}")

        # Static file serving
        @app.route('/', defaults={'path': ''})
        @app.route('/<path:path>')
        def serve(path):
            static_folder_path = app.static_folder
            if static_folder_path is None:
                return "Static folder not configured", 404

            if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
                return send_from_directory(static_folder_path, path)

            index_path = os.path.join(static_folder_path, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(static_folder_path, 'index.html')

            return "index.html not found", 404

    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)
