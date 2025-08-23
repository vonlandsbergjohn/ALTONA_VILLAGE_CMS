# fix_admin.py
import getpass
import logging
from werkzeug.security import generate_password_hash

# Use your app factory
from altona_village_cms.src.main import create_app

# 🟢 IMPORTANT: import the SAME db and User your models use
from altona_village_cms.src.models.user import db, User


def set_user_password(user, raw_password: str):
    """Set password in a way compatible with typical Flask user models."""
    # Prefer a model's own method if it exists
    if hasattr(user, "set_password") and callable(getattr(user, "set_password")):
        user.set_password(raw_password)
        return

    # Else, use Werkzeug's pbkdf2 hash and store it in common fields
    hashed = generate_password_hash(raw_password)

    if hasattr(user, "password_hash"):
        setattr(user, "password_hash", hashed)
        return

    if hasattr(user, "password"):
        setattr(user, "password", hashed)
        return

    raise RuntimeError(
        "Couldn't set password: no set_password(), password_hash, or password field found."
    )


def ensure_admin(email: str, password: str):
    logging.getLogger().setLevel(logging.INFO)

    print("➡️ Creating Flask app…")
    app = create_app()

    # Bind THIS db instance (from models.user) to the app
    print("➡️ Initializing db with app…")
    try:
        db.init_app(app)  # harmless if already bound inside create_app
    except Exception:
        pass

    print("➡️ Entering app context and ensuring tables exist…")
    with app.app_context():
        db.create_all()  # no-op if tables already exist

        print(f"➡️ Ensuring admin user exists for: {email}")
        session = db.session

        user = session.query(User).filter_by(email=email).first()
        if not user:
            user = User(email=email)

        # Ensure admin role + active status (adjust if your fields differ)
        if hasattr(user, "role"):
            user.role = "admin"
        if hasattr(user, "status"):
            user.status = "active"
        if hasattr(user, "is_active"):
            user.is_active = True

        set_user_password(user, password)

        session.add(user)
        session.commit()
        print("✅ Admin ensured. You can now log in with this email and password.")


if __name__ == "__main__":
    print("Admin email:", end=" ")
    email = input().strip()
    password = getpass.getpass("Admin password: ").strip()
    ensure_admin(email, password)
