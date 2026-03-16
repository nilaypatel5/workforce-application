from dataclasses import dataclass

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine

from config import Config

Base = declarative_base()

engine = create_engine(
    Config.DATABASE_URL,
    echo=False,
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

class UserORM(Base):
    __tablename__ = "Users"

    Id = Column(Integer, primary_key=True, index=True)
    Username = Column(String(50), unique=True, index=True, nullable=False)
    HashedPassword = Column(String(255), nullable=False)
    IsActive = Column(Boolean, nullable=False, default=True)


@dataclass
class User:
    username: str
    hashed_password: str
    is_active: bool = True