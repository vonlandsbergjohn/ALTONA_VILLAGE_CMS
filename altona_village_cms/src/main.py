# altona_village_cms/src/main.py
import os
import sys
import logging
from typing import Optional

# ---- Preserve your path setup (so `src.*` imports work) ---------------------
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from werkzeug.security import generate_password_hash

# Determine the correct project root for the .env file
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv(os.path.join(project_root, '.env'))
from src.models.user import db  # import db only here


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )

    # ---- CORS Setup ---------------------------------------------------------
    CORS(
        app,
        resources={r"/api/*": {"origins": ["http://localhost:3000", "http://localhost:3001"]}},
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=["Content-Type", "Authorization"]
    )

    # ---- Handle OPTIONS requests globally -----------------------------------
    @app.before_request
    def handle_options():
        if request.method == "OPTIONS":
            return ("", 204)

    # ---- Register auth blueprint --------------------------------------------
    try:
        from src.routes.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix="/api/auth")
    except Exception as e:
        app.logger.exception("Failed to register auth_bp: %s", e)

    # ---- Secrets & core config ---------------------------------------------
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "asdf#FGSgvasgf$5$WGT")
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "jwt-secret-string-change-in-production")
    app.config["BOOTSTRAP_KEY"] = os.environ.get("BOOTSTRAP_KEY", "")

    # ---- Database Configuration -------------------------------------------
    # Load from environment variable, with a fallback for local development.
    # The fallback is for convenience in a trusted local dev environment.
    # In production, DATABASE_URL *must* be set.
    db_url = os.getenv('DATABASE_URL')

    # Heroku/Render use `postgres://`, but SQLAlchemy needs `postgresql://`
    if not db_url:
        app.logger.error("DATABASE_URL environment variable not set.")
        raise ValueError("DATABASE_URL is not set. Please check your .env file or environment variables.")

    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    print(f"DEBUG: Connected to DB: {app.config['SQLALCHEMY_DATABASE_URI']}")

    # ---- Uploads -----------------------------------------------------------
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB
    upload_dir = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_dir

    # ---- Extensions --------------------------------------------------------
    JWTManager(app)
    db.init_app(app)

    # --- Create all database tables if they don't exist ---------------------
    with app.app_context():
        # This will create tables from all models imported in the project
        # (e.g., User, Property, Vehicle)
        db.create_all()

    # --- Ensure the `user_changes` table exists -----------------------------
    try:
        from src.models.user_change import ensure_user_changes_table
        with app.app_context():
            ensure_user_changes_table()
    except Exception as e:
        app.logger.exception("Failed to ensure user_changes table: %s", e)

    # ---- Logging -----------------------------------------------------------
    logging.basicConfig(level=logging.INFO)
    app.logger.info("App starting with DB: %s", app.config["SQLALCHEMY_DATABASE_URI"])

    # ---- Health check ------------------------------------------------------
    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"}), 200

    # ---- CLI command to initialize the database ----------------------------
    @app.cli.command("init-db")
    def init_db_command():
        """Creates the database tables."""
        try:
            db.create_all()
            from src.models.user_change import ensure_user_changes_table
            ensure_user_changes_table()
            print("Initialized the database and all tables.")
        except Exception as e:
            print(f"Error initializing database: {e}")
            # Optionally re-raise or handle more gracefully
            # raise e

    @app.cli.command("set-admin-password")
    def set_admin_password_command():
        """Finds or creates an admin user and sets a known password."""
        admin_email = "vonlandsbergjohn@gmail.com"
        new_password = "dGdFHLCJxx44ykq"  # A secure, known password for dev

        try:
            from src.models.user import User  # Import the User model here
            # Find all users with this email, regardless of role
            all_users = db.session.query(User).filter_by(email=admin_email).all()
            admin_user = next((u for u in all_users if u.role == 'admin'), None)

            if not admin_user:
                # If no admin user exists, create one
                print(f"Admin user '{admin_email}' not found. Creating a new one.")
                admin_user = User(email=admin_email, role='admin', status='active')
                db.session.add(admin_user)

            # 1. Set the admin user's password and ensure they are active
            admin_user.set_password(new_password)
            admin_user.status = 'active'
            print(f"✅ Admin user '{admin_user.email}' is being configured.")

            # 2. Disable any other conflicting non-admin users with the same email
            disabled_count = 0
            for user in all_users:
                if user.id != admin_user.id and user.role != 'admin':
                    user.status = 'inactive'  # Mark as inactive
                    # Set a long, random, unusable password
                    user.password_hash = generate_password_hash("disabled-user-placeholder-password")
                    print(f"   - Disabling conflicting non-admin account (ID: {user.id})")
                    disabled_count += 1

            db.session.commit()
            print("\n✅ Success! Admin credentials have been set.")
            print(f"   - Email:    {admin_email}")
            print(f"   - Password: {new_password}")
            if disabled_count > 0:
                print(f"   - Disabled {disabled_count} conflicting account(s).")

        except Exception as e:
            db.session.rollback()
            print(f"❌ An error occurred while setting admin password: {e}")

    # The app context is now needed for the init-db command to work

    # ---- Serve uploads -----------------------------------------------------
    @app.get("/uploads/<path:filename>")
    def uploaded_file(filename: str):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    # ---- Register blueprints -----------------------------------------------
    try:
        from src.routes.user import user_bp
        app.register_blueprint(user_bp, url_prefix="/api")
    except Exception as e:
        app.logger.exception("Failed to register user_bp: %s", e)

    try:
        from src.routes.admin import admin_bp
        app.register_blueprint(admin_bp, url_prefix="/api/admin")
    except Exception as e:
        app.logger.exception("Failed to register admin_bp: %s", e)

    try:
        from src.routes.resident import resident_bp
        app.register_blueprint(resident_bp, url_prefix="/api/resident")
    except Exception as e:
        app.logger.exception("Failed to register resident_bp: %s", e)

    try:
        from src.routes.communication import communication_bp
        app.register_blueprint(communication_bp, url_prefix="/api/communication")
    except Exception as e:
        app.logger.exception("Failed to register communication_bp: %s", e)

    try:
        from src.routes.gate_register import gate_register_bp
        app.register_blueprint(gate_register_bp, url_prefix="/api/admin")
    except Exception as e:
        app.logger.exception("Failed to register gate_register_bp: %s", e)

    try:
        from src.routes.admin_notifications import admin_notifications
        app.register_blueprint(admin_notifications, url_prefix="/api")
    except Exception as e:
        app.logger.exception("Failed to register admin_notifications: %s", e)

    try:
        if app.config.get("BOOTSTRAP_KEY"):
            from src.routes.bootstrap_admin import bootstrap_bp
            app.register_blueprint(bootstrap_bp)
            app.logger.info("bootstrap_admin route ENABLED")
    except Exception as e:
        app.logger.exception("Failed to register bootstrap_admin bp: %s", e)

    try:
        from src.routes.transition_requests import transition_bp
        app.register_blueprint(transition_bp, url_prefix="/api/transition")
    except Exception as e:
        app.logger.exception("Failed to register transition_bp: %s", e)

    try:
        from src.routes.public import public_bp
        app.register_blueprint(public_bp, url_prefix="/api/public")
    except Exception as e:
        app.logger.exception("Failed to register public_bp: %s", e)

    try:
        from src.routes.user_management import user_management_bp
        app.register_blueprint(user_management_bp, url_prefix="/api")
    except Exception as e:
        app.logger.exception("Failed to register user_management_bp: %s", e)

    return app


# Expose `app` for Gunicorn: "src.main:app"
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)