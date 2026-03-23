# Day 6 — Manager approvals + calendar UX

**Date:** 23-03-2026

## Goal

Complete leave management with a **manager approval flow**, **audit fields** for decisions, **validation** for overlapping approved leave, and a **month calendar** on My Leaves.

Adds to database:

* `Users.IsManager` — `BIT NOT NULL DEFAULT 0`
* `LeaveRequests`: `ApprovedByUserId`, `ApprovedAt`, `RejectedByUserId`, `RejectedAt`, `ManagerComment` (FKs to `Users`)

Grant manager access used this :

```sql
UPDATE dbo.Users SET IsManager = 1 WHERE Username = N'employee4';
```

**Note:** No need to log in again for manager APIs. `IsManager` is read from the database on each request. Refresh or reopen the app so **Team Leave Approvals** is visible after `GET /auth/me` returns `isManager: true`.

### Manager scope

* **Pending list** (`GET /manager/leaves/pending`): all **Pending** leave requests for **other employees**.
* **Approve / Reject**: manager can act on other employees’ requests, not their own.

If the table is empty, check that there is at least one **Pending** request from another user.

## Backend (Python / Flask)

File: `backend-flask/app.py`

| Method | Path                           | Purpose                                                 |
| ------ | ------------------------------ | ------------------------------------------------------- |
| GET    | `/auth/me`                     | Returns `username`, `isManager`, `department`           |
| GET    | `/ess/leaves`                  | Includes `managerComment`, `approvedAt`, `rejectedAt`   |
| POST   | `/ess/leaves`                  | Rejects if overlapping with existing **Approved** leave |
| GET    | `/manager/leaves/pending`      | Returns pending leaves (`403` if not manager)           |
| PUT    | `/manager/leaves/<id>/approve` | `{ "comment": "optional" }`                             |
| PUT    | `/manager/leaves/<id>/reject`  | Same body                                               |

File: `backend-flask/models.py` — includes `IsManager` and audit fields.

## Frontend (SAP UI5)

Path: `workforce-portal/webapp/`

* **manifest.json**: route `team-approvals`, includes `sap.ui.unified`
* **Main**: button visible when `isManager = true`
* **TeamLeaveApprovals**: approve/reject with optional comment
* **MyLeaves**: calendar view with `DateTypeRange`, day-wise table

## Quality checks

* Overlap validation on create (only against **Approved** leaves)
* Optional manager comment stored in `ManagerComment`

## My current data

* `employee1` → IT
* `employee2` → HR
* `employee3` → Finance
* `employee4` → Sales

Manager already set:

```sql
UPDATE dbo.Users SET IsManager = 1 WHERE Username = N'employee4';
```

If approvals list is empty, there are no pending leaves for other employees.

## SQL Used

```sql
-- 1) Check manager flag
SELECT Id, Username, IsManager
FROM dbo.Users
ORDER BY Id;

-- 2) Check employee mapping
SELECT Id, UserId, FirstName, LastName, Department
FROM dbo.Employees
ORDER BY Id;

-- 3) Check leave requests
SELECT
    lr.Id,
    u.Username,
    lr.EmployeeId,
    lr.StartDate,
    lr.EndDate,
    lr.Type,
    lr.Status,
    lr.Reason,
    lr.ManagerComment,
    lr.ApprovedAt,
    lr.RejectedAt
FROM dbo.LeaveRequests lr
JOIN dbo.Employees e ON e.Id = lr.EmployeeId
JOIN dbo.Users u ON u.Id = e.UserId
ORDER BY lr.Id DESC;
```

## Explanation

"I implemented a manager leave approval flow. Managers (`IsManager = 1`) can view pending requests from other employees and approve/reject them with comments. The system stores audit fields and comments. I also added a calendar view in My Leaves with highlighted ranges and day-level details."

---
