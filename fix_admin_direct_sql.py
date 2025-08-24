# fix_admin_direct_sql.py
import os
import sys
from typing import Optional
from sqlalchemy import create_engine, MetaData, Table, select, update, insert
from sqlalchemy.engine import Engine
from werkzeug.security import generate_password_hash

EMAIL = "vonlandsbergjohn@gmail.com"
RAW_PASSWORD = "dGdFHLCJxx44ykq"  # will be hashed before storing

def get_engine() -> Engine:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("❌ DATABASE_URL env var not set.")
        sys.exit(1)
    # Engine with pre_ping to avoid stale connections
    return create_engine(url, pool_pre_ping=True)

def find_users_table(md: MetaData) -> Optional[Table]:
    # Common table names
    for name in ("users", "user"):
        if name in md.tables:
            return md.tables[name]
    return None

def main():
    engine = get_engine()
    md = MetaData()
    md.reflect(bind=engine)

    users = find_users_table(md)
    if users is None:
        print("❌ Could not find a 'users' or 'user' table in the database.")
        print("   Found tables:", ", ".join(sorted(md.tables.keys())))
        sys.exit(1)

    cols = users.c.keys()
    if "email" not in cols:
        print("❌ The users table has no 'email' column. Columns are:", cols)
        sys.exit(1)

    # Choose a password column
    pwd_col = "password_hash" if "password_hash" in cols else ("password" if "password" in cols else None)
    if pwd_col is None:
        print("❌ No 'password_hash' or 'password' column found. Columns are:", cols)
        sys.exit(1)

    # Optional columns
    role_col = "role" if "role" in cols else None
    status_col = "status" if "status" in cols else None
    active_col = "is_active" if "is_active" in cols else None

    hashed = generate_password_hash(RAW_PASSWORD)

    with engine.begin() as conn:
        # Check if the user exists
        existing = conn.execute(
            select(users).where(users.c.email == EMAIL)
        ).fetchone()

        values = { "email": EMAIL, pwd_col: hashed }
        if role_col:   values[role_col] = "admin"
        if status_col: values[status_col] = "active"
        if active_col: values[active_col] = True

        if existing:
            # Update
            conn.execute(
                update(users)
                .where(users.c.email == EMAIL)
                .values(**values)
            )
            print("✅ Updated existing admin:", EMAIL)
        else:
            # Insert
            conn.execute(
                insert(users).values(**values)
            )
            print("✅ Inserted new admin:", EMAIL)

        # Read-back confirmation (masked)
        result = conn.execute(
            select(users.c.email, *(c for c in users.c if c.key in (role_col, status_col, active_col) if c is not None))
            .where(users.c.email == EMAIL)
        ).fetchone()
        print("ℹ️  Row after write:", dict(result) if result else None)

if __name__ == "__main__":
    main()
