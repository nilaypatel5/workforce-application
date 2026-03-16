from sqlalchemy import text

from config import Config
from models import engine

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).fetchone()
        print("Connection successful!", result)
except Exception as e:
    print("Connection failed:", e)