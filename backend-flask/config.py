import os

class Config:
    # JWT / secret settings
    SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_ME_DEV_ONLY")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRES_MINUTES = 60

    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        DATABASE_URL = (
            "mssql+pyodbc://localhost/EmployeeAuth"
            "?driver=ODBC+Driver+18+for+SQL+Server"
            "&trusted_connection=yes"
            "&TrustServerCertificate=yes"
        )
