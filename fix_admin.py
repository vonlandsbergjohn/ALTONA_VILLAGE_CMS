# fix_admin.py
import os
from getpass import getpass
from importlib import import_module
from werkzeug.security import generate_password_hash

# Prefer env vars if you don't want to type each time
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL") or input("Admin email: ").strip()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD") or getpass("Admin password: ")

# Import your app module and reuse the existing app if present
main_mod = import_module("altona_village_cms.src.main")
app = getattr(main_mod, "app", None) or main_mod.create_app()

# Import models/db after app module so paths are set up
from altona_village_cms.src.models.user import db, User  # noqa: E402


def ensure_admin(email: str, password: str) -> None:
    with app.app_context():
        u = User.query.filter_by(email=email).first()
        if not u:
            u = User(
                email=email,
                role="admin",
                status="active",
                password_hash=generate_password_hash(password),
            )
            db.session.add(u)
            db.session.commit()
            print(f"✅ Created admin user {email} (id={u.id})")
        else:
            u.role = "admin"
            u.status = "active"
            u.password_hash = generate_password_hash(password)
            db.session.commit()
            print(f"✅ Updated existing admin user {email} (id={u.id})")


if __name__ == "__main__":
    ensure_admin(ADMIN_EMAIL, ADMIN_PASSWORD)
