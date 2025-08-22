# fix_admin.py (run from your repo root)
import os
import argparse
from getpass import getpass

# Import your Flask app factory
from altona_village_cms.src.main import create_app

# Import your models/db (these rely on the app context)
from src.models.user import db, User


def ensure_admin(email: str, password: str):
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            # Create new admin
            user = User(email=email, role="admin", status="active")
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            print(f"[OK] Created admin user: {email}")
        else:
            # Update existing user to admin/active and set password
            user.role = "admin"
            user.status = "active"
            if password:
                user.set_password(password)
            db.session.commit()
            print(f"[OK] Updated existing user to admin/active: {email}")

        print(f"-> id={user.id}  role={user.role}  status={user.status}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create or repair the admin user")
    parser.add_argument("--email", default=os.environ.get("ADMIN_EMAIL"), help="Admin email")
    parser.add_argument("--password", default=os.environ.get("ADMIN_PASSWORD"), help="Admin password")

    args = parser.parse_args()

    email = args.email or input("Admin email: ").strip()
    password = args.password or getpass("Admin password: ").strip()

    if not email or not password:
        raise SystemExit("Email and password are required.")

    ensure_admin(email, password)
