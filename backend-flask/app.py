from functools import wraps

import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from jose import jwt, JWTError
from sqlalchemy import text

from config import Config
from auth_service import authenticate_user, create_user_token, DatabaseUnavailableError
from models import (
    SessionLocal,
    UserORM,
    EmployeeORM,
    EmployeeProfile,
    engine,
)

app = Flask(__name__)
app.config.from_object(Config)

# Allow your UI5 origin(s)
_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:8080").split(",")
_cors_origins = [o.strip() for o in _cors_origins if o.strip()]
CORS(app, origins=_cors_origins)


@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Flask backend running"})


@app.route("/db/health", methods=["GET"])
def db_health():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).fetchone()
        return jsonify({"status": "ok", "db": "connected", "result": list(result) if result else None})
    except Exception:
        return jsonify({"status": "error", "db": "unreachable"}), 503


@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password required"}), 400

    try:
        user = authenticate_user(username, password)
    except DatabaseUnavailableError:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Database is not reachable. Check SQL Server and DATABASE_URL.",
                }
            ),
            503,
        )
    if not user:
        return jsonify({"success": False, "message": "Invalid username or password"}), 401

    token = create_user_token(user)
    return jsonify({"success": True, "token": token, "message": "Login successful"}), 200


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"detail": "Not authenticated"}), 401

        token = auth_header.split(" ", 1)[1]

        try:
            payload = jwt.decode(
                token,
                Config.SECRET_KEY,
                algorithms=[Config.JWT_ALGORITHM],
            )
            username = payload.get("sub")
            if not username:
                raise JWTError("No subject in token")
        except JWTError:
            return jsonify({"detail": "Invalid or expired token"}), 401

        return f(username=username, *args, **kwargs)

    return decorated


@app.route("/auth/me", methods=["GET"])
@token_required
def who_am_i(username):
    return jsonify({"username": username})


@app.route("/ess/profile", methods=["GET"])
@token_required
def my_profile(username):
    username = (username or "").strip().lower()  # ✅ FIX ADDED

    with SessionLocal() as session:
        user = session.query(UserORM).filter(UserORM.Username.ilike(username)).one_or_none()  # ✅ FIXED
        if user is None:
            return jsonify({"detail": "User not found"}), 404

        employee = (
            session.query(EmployeeORM)
            .filter(EmployeeORM.UserId == user.Id)
            .one_or_none()
        )
        if employee is None:
            return jsonify({"detail": "Employee profile not found"}), 404

        profile = EmployeeProfile(
            first_name=employee.FirstName,
            last_name=employee.LastName,
            email=employee.Email,
            phone=employee.Phone,
            department=employee.Department,
        )

        return jsonify(
            {
                "firstName": profile.first_name,
                "lastName": profile.last_name,
                "email": profile.email,
                "phone": profile.phone,
                "department": profile.department,
            }
        )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)