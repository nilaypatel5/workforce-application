from models import SessionLocal, UserORM
from security import get_password_hash

# This will hash all plain-text passwords in the database
with SessionLocal() as session:
    users = session.query(UserORM).all()
    for user in users:

        if not (user.HashedPassword or "").startswith("$2"):
            original = user.HashedPassword
            user.HashedPassword = get_password_hash(original)
            print(f"Hashed password for user: {user.Username}")
    session.commit()

print("All passwords updated to hashed versions.")