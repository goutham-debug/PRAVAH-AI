"""Administration CLI (run on the server, not exposed over HTTP).

  python manage.py create-user      interactive; creates a user with a chosen role
  python manage.py init-db          create tables (idempotent)
"""
import getpass
import sys
from datetime import datetime

from app import app  # noqa: F401  (initialises config + database)
from database import SessionLocal, init_db
from models import User
from security import ROLES, hash_password, validate_password_strength


def create_user():
    email = input("Email: ").strip().lower()
    name = input("Full name: ").strip()
    print("Roles:", ", ".join(ROLES))
    role = input("Role: ").strip().upper()
    if role not in ROLES or '@' not in email or not name:
        sys.exit("Invalid email, name or role.")
    pw = getpass.getpass("Temporary password: ")
    problem = validate_password_strength(pw, email)
    if problem:
        sys.exit(problem)
    s = SessionLocal()
    try:
        if s.query(User).filter(User.email == email).first():
            sys.exit("User already exists.")
        s.add(User(email=email, full_name=name, role=role, password_hash=hash_password(pw),
                   must_change_password=True, password_changed_at=datetime.utcnow()))
        s.commit()
        print("Created. The user must change this password at first sign-in.")
    finally:
        s.close()


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'create-user':
        create_user()
    elif cmd == 'init-db':
        init_db()
        print("Database initialised.")
    else:
        print(__doc__)
