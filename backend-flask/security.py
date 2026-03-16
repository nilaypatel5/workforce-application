from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt
from passlib.context import CryptContext

from config import Config

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    if expires_minutes is None:
        expires_minutes = Config.JWT_EXPIRES_MINUTES

    now_utc = datetime.now(timezone.utc)

    to_encode = {
        "sub": subject,
        "exp": now_utc + timedelta(minutes=expires_minutes),
        "iat": now_utc,
    }

    encoded_jwt = jwt.encode(
        to_encode,
        Config.SECRET_KEY,
        algorithm=Config.JWT_ALGORITHM,
    )
    return encoded_jwt