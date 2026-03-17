from dataclasses import dataclass

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
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

    Employee = relationship("EmployeeORM", back_populates="User", uselist=False)


class EmployeeORM(Base):
    __tablename__ = "Employees"

    Id = Column(Integer, primary_key=True, index=True)
    UserId = Column(Integer, ForeignKey("Users.Id"), nullable=False)
    FirstName = Column(String(50), nullable=False)
    LastName = Column(String(50), nullable=False)
    Email = Column(String(100), nullable=False)
    Phone = Column(String(20), nullable=True)
    Department = Column(String(50), nullable=True)
    CreatedAt = Column(DateTime(timezone=True), nullable=False, server_default=func.sysdatetime())

    User = relationship("UserORM", back_populates="Employee")


@dataclass
class User:
    username: str
    hashed_password: str
    is_active: bool = True


@dataclass
class EmployeeProfile:
    first_name: str
    last_name: str
    email: str
    phone: str | None
    department: str | None