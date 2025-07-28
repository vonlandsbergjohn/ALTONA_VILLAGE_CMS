from altona_village_cms.src.models.user import User, db
from altona_village_cms.src.main import app

with app.app_context():
    users = User.query.all()
    print("Existing users:")
    for user in users:
        print(f"Email: {user.email}, Role: {user.role}, Status: {user.status}")
