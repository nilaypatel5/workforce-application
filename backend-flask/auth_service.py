from typing import Optional

from sqlalchemy import select

from models import User, UserORM, SessionLocal
from security import verify_password, get_password_hash, create_access_token


def get_user_by_username(username: str) -> Optional[User]:
    with SessionLocal() as session:
        stmt = select(UserORM).where(UserORM.Username == username)
        result = session.execute(stmt).scalar_one_or_none()
        if result is None:
            return None
        return User(
            username=result.Username,
            hashed_password=result.HashedPassword,
            is_active=result.IsActive,
        )


def authenticate_user(username: str, password: str) -> Optional[User]:
    """
    Authenticate against the Users table.

    Supports a safe migration path:
    - If `HashedPassword` is a bcrypt hash (starts with "$2"), verify with passlib.
    - If `HashedPassword` is still plain-text (legacy), compare directly once and
      upgrade it in-place to a bcrypt hash on successful login.
    """
    username = (username or "").strip()
    if not username:
        return None

    with SessionLocal() as session:
        stmt = select(UserORM).where(UserORM.Username == username)
        orm_user = session.execute(stmt).scalar_one_or_none()
        if orm_user is None:
            return None
        if not orm_user.IsActive:
            return None

        stored = orm_user.HashedPassword or ""

        # bcrypt hashes commonly start with $2a$, $2b$, or $2y$ (all begin with "$2")
        if stored.startswith("$2"):
            if not verify_password(password, stored):
                return None
        else:
            # Legacy plain-text fallback + auto-upgrade
            if password != stored:
                return None
            orm_user.HashedPassword = get_password_hash(password)
            session.commit()

        return User(
            username=orm_user.Username,
            hashed_password=orm_user.HashedPassword,
            is_active=orm_user.IsActive,
        )


def create_user_token(user: User) -> str:
    return create_access_token(subject=user.username)