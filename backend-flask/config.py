import os
from pathlib import Path

try:
    from dotenv import load_dotenv  # type: ignore
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv(dotenv_path=Path(__file__).with_name(".env"), override=False)

class Config:
    # JWT / secret settings
    SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_ME_DEV_ONLY")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRES_MINUTES = 60

    # Database
    # Prefer an explicit DATABASE_URL if provided (recommended).
    DATABASE_URL = os.getenv("DATABASE_URL")

    # If DATABASE_URL is not set, build a reasonable default for local SQL Server Express.
    # Supports instance names like: Nilay\SQLEXPRESS
    if not DATABASE_URL:
        db_server = os.getenv("DB_SERVER", r"Nilay\SQLEXPRESS")
        db_name = os.getenv("DB_NAME", "EmployeeAuth")
        db_driver = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")

        # Important: For SQL Server instance names, the server must be passed as host.
        # SQLAlchemy/pyodbc expects backslash in the host portion as-is.
        DATABASE_URL = (
            f"mssql+pyodbc://{db_server}/{db_name}"
            f"?driver={db_driver.replace(' ', '+')}"
            "&trusted_connection=yes"
            "&TrustServerCertificate=yes"
        )
