# add_test_change.py — local test that doesn't require existing users table

from src.main import app
from src.models.user import db  # keeps the app context + session available
from src.routes.admin_notifications import log_user_change

with app.app_context():
    ok = log_user_change(
        user_id="LOCAL_TEST",           # arbitrary string; no FK enforced
        user_name="Local Debug",        # just for readability in logs
        erf_number="27727",             # something your UI would show
        change_type="user_add",         # matches your “critical” types
        field_name="vehicle_registration",
        old_value=None,
        new_value="ZZZ999",             # any value
    )
    print("Inserted change" if ok else "Failed to insert change")
