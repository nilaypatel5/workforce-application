from dataclasses import dataclass

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
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
    IsManager = Column(Boolean, nullable=False, default=False)

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
    LeaveRequests = relationship("LeaveRequestORM", back_populates="Employee")


class LeaveRequestORM(Base):
    """
    Maps to the LeaveRequests table in SQL Server.

    Optional columns (Day 6 migration): ApprovedByUserId, ApprovedAt, RejectedByUserId,
    RejectedAt, ManagerComment — see migrations/day6_manager_and_audit.sql.
    """

    __tablename__ = "LeaveRequests"

    Id = Column(Integer, primary_key=True, index=True)
    EmployeeId = Column(Integer, ForeignKey("Employees.Id"), nullable=False, index=True)
    StartDate = Column(Date, nullable=False)
    EndDate = Column(Date, nullable=False)
    Type = Column(String(50), nullable=False)
    Status = Column(String(20), nullable=False, default="Pending")
    Reason = Column(String(500), nullable=True)
    CreatedAt = Column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.sysdatetime(),
    )
    ApprovedByUserId = Column(Integer, ForeignKey("Users.Id"), nullable=True)
    ApprovedAt = Column(DateTime(timezone=False), nullable=True)
    RejectedByUserId = Column(Integer, ForeignKey("Users.Id"), nullable=True)
    RejectedAt = Column(DateTime(timezone=False), nullable=True)
    ManagerComment = Column(String(500), nullable=True)

    Employee = relationship("EmployeeORM", back_populates="LeaveRequests")


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

