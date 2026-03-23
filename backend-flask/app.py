from functools import wraps

import os
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from flask_cors import CORS
from jose import jwt, JWTError
from sqlalchemy import text, func

from config import Config
from auth_service import authenticate_user, create_user_token, DatabaseUnavailableError
from models import (
    SessionLocal,
    UserORM,
    EmployeeORM,
    EmployeeProfile,
    LeaveRequestORM,
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


def _leave_to_json(row: LeaveRequestORM, employee: EmployeeORM | None = None) -> dict:
    out: dict = {
        "id": row.Id,
        "startDate": row.StartDate.isoformat() if row.StartDate else "",
        "endDate": row.EndDate.isoformat() if row.EndDate else "",
        "type": row.Type,
        "status": row.Status,
        "reason": row.Reason,
        "createdAt": row.CreatedAt.isoformat() if row.CreatedAt else None,
        "managerComment": row.ManagerComment,
        "approvedAt": row.ApprovedAt.isoformat() if row.ApprovedAt else None,
        "rejectedAt": row.RejectedAt.isoformat() if row.RejectedAt else None,
    }
    if employee is not None:
        out["employeeId"] = employee.Id
        out["employeeName"] = f"{employee.FirstName} {employee.LastName}".strip()
        out["department"] = employee.Department
    return out


def _utc_naive_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _get_user_employee(session, username: str):
    username = (username or "").strip().lower()
    user = (
        session.query(UserORM)
        .filter(UserORM.Username.ilike(username))
        .one_or_none()
    )
    if user is None:
        return None, None
    employee = (
        session.query(EmployeeORM)
        .filter(EmployeeORM.UserId == user.Id)
        .one_or_none()
    )
    return user, employee


def _manager_can_act_on_leave(
    mgr_emp: EmployeeORM,
    target_emp: EmployeeORM,
    leave: LeaveRequestORM,
) -> bool:
    """Managers may approve/reject any other employee's request (not their own)."""
    if leave.EmployeeId == mgr_emp.Id:
        return False
    return target_emp.Id == leave.EmployeeId


def _normalized_status_expr():
    """Case/space-insensitive status expression for SQL Server filtering."""
    return func.lower(func.ltrim(func.rtrim(LeaveRequestORM.Status)))


@app.route("/auth/me", methods=["GET"])
@token_required
def who_am_i(username):
    username = (username or "").strip().lower()
    with SessionLocal() as session:
        user, employee = _get_user_employee(session, username)
        if user is None:
            return jsonify({"detail": "User not found"}), 404
        payload = {
            "username": user.Username,
            "isManager": bool(user.IsManager),
            "department": employee.Department if employee else None,
        }
        return jsonify(payload)


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

        return jsonify([_leave_to_json(row, None) for row in leave_rows])


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

        overlap = (
            session.query(LeaveRequestORM)
            .filter(
                LeaveRequestORM.EmployeeId == employee.Id,
                _normalized_status_expr() == "approved",
                LeaveRequestORM.StartDate <= end_date,
                LeaveRequestORM.EndDate >= start_date,
            )
            .first()
        )
        if overlap is not None:
            return (
                jsonify(
                    {
                        "detail": "This request overlaps an existing Approved leave. "
                        "Adjust your dates or cancel the other request first.",
                    }
                ),
                400,
            )

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

        return jsonify(_leave_to_json(new_leave, None)), 201


@app.route("/ess/leaves/<int:leave_id>/cancel", methods=["PUT"])
@token_required
def cancel_leave(username, leave_id: int):
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

        leave = (
            session.query(LeaveRequestORM)
            .filter(
                LeaveRequestORM.Id == leave_id,
                LeaveRequestORM.EmployeeId == employee.Id,
            )
            .one_or_none()
        )
        if leave is None:
            return jsonify({"detail": "Leave request not found"}), 404

        if (leave.Status or "").strip().lower() != "pending":
            return (
                jsonify(
                    {
                        "detail": "Only Pending leave requests can be cancelled",
                    }
                ),
                400,
            )

        leave.Status = "Cancelled"
        session.commit()
        session.refresh(leave)

        return jsonify(_leave_to_json(leave, None)), 200


@app.route("/manager/leaves/pending", methods=["GET"])
@token_required
def manager_pending_leaves(username):
    with SessionLocal() as session:
        user, mgr_emp = _get_user_employee(session, username)
        if user is None:
            return jsonify({"detail": "User not found"}), 404
        if not user.IsManager:
            return jsonify({"detail": "Manager role required"}), 403
        if mgr_emp is None:
            return jsonify({"detail": "Employee profile not found"}), 404

        q = (
            session.query(LeaveRequestORM, EmployeeORM)
            .join(EmployeeORM, LeaveRequestORM.EmployeeId == EmployeeORM.Id)
            .filter(
                _normalized_status_expr() == "pending",
                LeaveRequestORM.EmployeeId != mgr_emp.Id,
            )
        )

        rows = q.order_by(
            LeaveRequestORM.StartDate.asc(),
            LeaveRequestORM.Id.asc(),
        ).all()

        return jsonify(
            [_leave_to_json(leave_row, emp_row) for leave_row, emp_row in rows]
        )


@app.route("/manager/leaves/<int:leave_id>/approve", methods=["PUT"])
@token_required
def manager_approve_leave(username, leave_id: int):
    body = request.get_json(silent=True) or {}
    raw_comment = (body.get("comment") or "").strip()
    manager_comment = raw_comment or None

    with SessionLocal() as session:
        user, mgr_emp = _get_user_employee(session, username)
        if user is None:
            return jsonify({"detail": "User not found"}), 404
        if not user.IsManager:
            return jsonify({"detail": "Manager role required"}), 403
        if mgr_emp is None:
            return jsonify({"detail": "Employee profile not found"}), 404

        leave = (
            session.query(LeaveRequestORM)
            .filter(LeaveRequestORM.Id == leave_id)
            .one_or_none()
        )
        if leave is None:
            return jsonify({"detail": "Leave request not found"}), 404

        target_emp = (
            session.query(EmployeeORM)
            .filter(EmployeeORM.Id == leave.EmployeeId)
            .one_or_none()
        )
        if target_emp is None:
            return jsonify({"detail": "Employee not found"}), 404

        if not _manager_can_act_on_leave(mgr_emp, target_emp, leave):
            return jsonify({"detail": "Not allowed to act on this leave request"}), 403

        if (leave.Status or "").strip().lower() != "pending":
            return (
                jsonify({"detail": "Only Pending leave requests can be approved"}),
                400,
            )

        overlap = (
            session.query(LeaveRequestORM)
            .filter(
                LeaveRequestORM.EmployeeId == leave.EmployeeId,
                _normalized_status_expr() == "approved",
                LeaveRequestORM.Id != leave.Id,
                LeaveRequestORM.StartDate <= leave.EndDate,
                LeaveRequestORM.EndDate >= leave.StartDate,
            )
            .first()
        )
        if overlap is not None:
            return (
                jsonify(
                    {
                        "detail": "Another Approved leave already overlaps this date range.",
                    }
                ),
                409,
            )

        now = _utc_naive_now()
        leave.Status = "Approved"
        leave.ApprovedByUserId = user.Id
        leave.ApprovedAt = now
        leave.RejectedByUserId = None
        leave.RejectedAt = None
        leave.ManagerComment = manager_comment

        session.commit()
        session.refresh(leave)

        return jsonify(_leave_to_json(leave, target_emp)), 200


@app.route("/manager/leaves/<int:leave_id>/reject", methods=["PUT"])
@token_required
def manager_reject_leave(username, leave_id: int):
    body = request.get_json(silent=True) or {}
    raw_comment = (body.get("comment") or "").strip()
    manager_comment = raw_comment or None

    with SessionLocal() as session:
        user, mgr_emp = _get_user_employee(session, username)
        if user is None:
            return jsonify({"detail": "User not found"}), 404
        if not user.IsManager:
            return jsonify({"detail": "Manager role required"}), 403
        if mgr_emp is None:
            return jsonify({"detail": "Employee profile not found"}), 404

        leave = (
            session.query(LeaveRequestORM)
            .filter(LeaveRequestORM.Id == leave_id)
            .one_or_none()
        )
        if leave is None:
            return jsonify({"detail": "Leave request not found"}), 404

        target_emp = (
            session.query(EmployeeORM)
            .filter(EmployeeORM.Id == leave.EmployeeId)
            .one_or_none()
        )
        if target_emp is None:
            return jsonify({"detail": "Employee not found"}), 404

        if not _manager_can_act_on_leave(mgr_emp, target_emp, leave):
            return jsonify({"detail": "Not allowed to act on this leave request"}), 403

        if (leave.Status or "").strip().lower() != "pending":
            return (
                jsonify({"detail": "Only Pending leave requests can be rejected"}),
                400,
            )

        now = _utc_naive_now()
        leave.Status = "Rejected"
        leave.RejectedByUserId = user.Id
        leave.RejectedAt = now
        leave.ApprovedByUserId = None
        leave.ApprovedAt = None
        leave.ManagerComment = manager_comment

        session.commit()
        session.refresh(leave)

        return jsonify(_leave_to_json(leave, target_emp)), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)