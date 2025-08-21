# fix_admin.py
import os, sys, getpass
# make "altona_village_cms/src" importable
ROOT = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(ROOT, "altona_village_cms"))
sys.path.insert(0, os.path.join(ROOT, "altona_village_cms", "src"))

from altona_village_cms.src.main import create_app
from altona_village_cms.src.models.user import db, User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    email = input("Admin email: ").strip().lower()
    pwd = getpass.getpass("Admin password: ").strip()

    u = User.query.filter_by(email=email).first()
    created = False
    if not u:
        u = User(email=email)
        db.session.add(u)
        created = True

    u.password_hash = generate_password_hash(pwd)
    u.role = "admin"
    for field, value in [
        ("status", "active"),
        ("is_active", True),
        ("approved", True),
        ("is_approved", True),
        ("approval_status", "approved"),
    ]:
        if hasattr(u, field):
            setattr(u, field, value)

    db.session.commit()
    print(f"✅ {'Created' if created else 'Updated'} admin:", email)
