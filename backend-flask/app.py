from functools import wraps

import os
from datetime import datetime
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
    LeaveRequestORM,
    LeaveRequest,
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
        return jsonify(
            {"status": "ok", "db": "connected", "result": list(result) if result else None}
        )
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
    username = (username or "").strip().lower()

    with SessionLocal() as session:
        user = (
            session.query(UserORM)
            .filter(UserORM.Username.ilike(username))
            .one_or_none()
        )
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


@app.route("/ess/leaves", methods=["GET"])
@token_required
def my_leaves(username):
    username = (username or "").strip().lower()

    with SessionLocal() as session:
        user = (
            session.query(UserORM)
            .filter(UserORM.Username.ilike(username))
            .one_or_none()
        )
        if user is None:
            return jsonify({"detail": "User not found"}), 404

        employee = (
            session.query(EmployeeORM)
            .filter(EmployeeORM.UserId == user.Id)
            .one_or_none()
        )
        if employee is None:
            return jsonify({"detail": "Employee profile not found"}), 404

        leave_rows = (
            session.query(LeaveRequestORM)
            .filter(LeaveRequestORM.EmployeeId == employee.Id)
            .order_by(LeaveRequestORM.StartDate.desc(), LeaveRequestORM.Id.desc())
            .all()
        )

        leaves: list[LeaveRequest] = []
        for row in leave_rows:
            leaves.append(
                LeaveRequest(
                    id=row.Id,
                    start_date=row.StartDate.isoformat() if row.StartDate else "",
                    end_date=row.EndDate.isoformat() if row.EndDate else "",
                    type=row.Type,
                    status=row.Status,
                    reason=row.Reason,
                )
            )

        return jsonify(
            [
                {
                    "id": leave.id,
                    "startDate": leave.start_date,
                    "endDate": leave.end_date,
                    "type": leave.type,
                    "status": leave.status,
                    "reason": leave.reason,
                }
                for leave in leaves
            ]
        )


@app.route("/ess/leaves", methods=["POST"])
@token_required
def create_leave(username):
    username = (username or "").strip().lower()
    body = request.get_json(silent=True) or {}

    raw_start = (body.get("startDate") or "").strip()
    raw_end = (body.get("endDate") or "").strip()
    leave_type = (body.get("type") or "").strip()
    reason = (body.get("reason") or "").strip() or None

    if not raw_start or not raw_end or not leave_type:
        return (
            jsonify(
                {
                    "detail": "startDate, endDate and type are required",
                }
            ),
            400,
        )

    try:
        start_date = datetime.fromisoformat(raw_start).date()
        end_date = datetime.fromisoformat(raw_end).date()
    except ValueError:
        return (
            jsonify(
                {
                    "detail": "startDate and endDate must be valid ISO dates (YYYY-MM-DD)",
                }
            ),
            400,
        )

    if end_date < start_date:
        return (
            jsonify(
                {
                    "detail": "endDate cannot be before startDate",
                }
            ),
            400,
        )

    with SessionLocal() as session:
        user = (
            session.query(UserORM)
            .filter(UserORM.Username.ilike(username))
            .one_or_none()
        )
        if user is None:
            return jsonify({"detail": "User not found"}), 404

        employee = (
            session.query(EmployeeORM)
            .filter(EmployeeORM.UserId == user.Id)
            .one_or_none()
        )
        if employee is None:
            return jsonify({"detail": "Employee profile not found"}), 404

        new_leave = LeaveRequestORM(
            EmployeeId=employee.Id,
            StartDate=start_date,
            EndDate=end_date,
            Type=leave_type,
            Status="Pending",
            Reason=reason,
        )
        session.add(new_leave)
        session.commit()
        session.refresh(new_leave)

        response = {
            "id": new_leave.Id,
            "startDate": new_leave.StartDate.isoformat() if new_leave.StartDate else "",
            "endDate": new_leave.EndDate.isoformat() if new_leave.EndDate else "",
            "type": new_leave.Type,
            "status": new_leave.Status,
            "reason": new_leave.Reason,
        }

        return jsonify(response), 201


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)