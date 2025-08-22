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

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from src.models.user import db  # import db only here


def _normalize_database_url(url: Optional[str]) -> Optional[str]:
    """
    Render/Postgres sometimes provides DATABASE_URL starting with 'postgres://'.
    SQLAlchemy prefers 'postgresql+psycopg2://' (or 'postgresql://').
    """
    if not url:
        return url
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    return url


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )

    # ---- Secrets & core config ---------------------------------------------
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "asdf#FGSgvasgf$5$WGT")
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "jwt-secret-string-change-in-production")
    app.config["BOOTSTRAP_KEY"] = os.environ.get("BOOTSTRAP_KEY", "")

    # Database
    db_url = _normalize_database_url(os.environ.get("DATABASE_URL"))
    if db_url:
        app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    else:
        # Local/dev fallback (file goes under src/database/)
        db_dir = os.path.join(os.path.dirname(__file__), "database")
        os.makedirs(db_dir, exist_ok=True)
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(db_dir, 'app.db')}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Uploads
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB
    upload_dir = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_dir

    # ---- Extensions ---------------------------------------------------------
    cors_origins_raw = os.environ.get("CORS_ORIGINS", "*")
    cors_origins = [o.strip() for o in cors_origins_raw.split(",")] if cors_origins_raw else ["*"]
    CORS(
        app,
        resources={r"/api/*": {"origins": cors_origins}},
        supports_credentials=True,
    )
    JWTManager(app)
    db.init_app(app)

    # ---- Logging (helpful in Render logs) -----------------------------------
    logging.basicConfig(level=logging.INFO)
    app.logger.info("App starting with DB: %s", app.config["SQLALCHEMY_DATABASE_URI"])

    # ---- Health check -------------------------------------------------------
    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"}), 200

    # ---- Serve uploads (optional) ------------------------------------------
    @app.get("/uploads/<path:filename>")
    def uploaded_file(filename: str):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    # ---- Import & register blueprints AFTER app exists ----------------------
    # (Keeps imports light at module import time and avoids circular refs)
    try:
        from src.routes.user import user_bp
        app.register_blueprint(user_bp, url_prefix="/api")
    except Exception as e:
        app.logger.exception("Failed to register user_bp: %s", e)

    try:
        from src.routes.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix="/api/auth")
    except Exception as e:
        app.logger.exception("Failed to register auth_bp: %s", e)

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
        # Note: this blueprint is named 'admin_notifications' (no _bp) in your project
        from src.routes.admin_notifications import admin_notifications
        app.register_blueprint(admin_notifications, url_prefix="/api")
    except Exception as e:
        app.logger.exception("Failed to register admin_notifications: %s", e)

    # Optional admin bootstrap/repair route:
    # Only enabled when BOOTSTRAP_KEY is set (prevents random usage).
    try:
        if app.config.get("BOOTSTRAP_KEY"):
            from src.routes.bootstrap_admin import bootstrap_bp
            app.register_blueprint(bootstrap_bp)  # route file defines its own paths
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
    # Local dev runner
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
