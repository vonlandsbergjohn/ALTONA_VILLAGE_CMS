# fix_admin.py  (put this at the repo root: C:\Altona_Village_CMS\fix_admin.py)
import getpass
from altona_village_cms.src.main import create_app
from altona_village_cms.src.models.user import db, User

def ensure_admin(email: str, password: str) -> None:
    app = create_app()
    with app.app_context():
        # Make sure all tables exist (works even after you delete app.db)
        db.create_all()

        user = User.query.filter_by(email=email).first()
        created = False
        if not user:
            user = User(email=email)
            db.session.add(user)
            created = True

        # Set admin + active, and flip any “approval” flags your model might use
        user.role = "admin"
        user.status = "active"
        if hasattr(user, "approved"): user.approved = True
        if hasattr(user, "is_approved"): user.is_approved = True
        if hasattr(user, "approval_status"): user.approval_status = "approved"

        # Set password
        if hasattr(user, "set_password"):
            user.set_password(password)
        else:
            # If your model uses password_hash directly:
            from werkzeug.security import generate_password_hash
            user.password_hash = generate_password_hash(password)

        db.session.commit()

        print(f"[OK] {'Created' if created else 'Updated'} admin user: {email}")
        print(f"-> id={user.id}  role={user.role}  status={user.status}")

if __name__ == "__main__":
    email = input("Admin email: ")
    password = getpass.getpass("Admin password: ")
    ensure_admin(email, password)
