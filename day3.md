# Day 3 — ESS “My Leaves” (List + Request)

**Date:** 18-03-2026

## Database Work (SSMS)

- **New table: `LeaveRequests`**
  - Created in `EmployeeAuth` database with:
    - `Id` INT IDENTITY(1,1) PRIMARY KEY
    - `EmployeeId` INT NOT NULL FOREIGN KEY REFERENCES `Employees(Id)`
    - `StartDate` DATE NOT NULL
    - `EndDate` DATE NOT NULL
    - `Type` NVARCHAR(50) NOT NULL
    - `Status` NVARCHAR(20) NOT NULL DEFAULT `'Pending'`
    - `Reason` NVARCHAR(500) NULL
    - `CreatedAt` DATETIME2 NOT NULL DEFAULT `SYSDATETIME()`

## Backend (Python / Flask)

Files in `backend-flask/`.

- **`models.py`**
  - Added `LeaveRequestORM` mapping for `LeaveRequests` table:
    - Matches the SQL schema above (types, lengths, defaults).
    - New relationship: `EmployeeORM.LeaveRequests` ↔ `LeaveRequestORM.Employee`.
  - Added `LeaveRequest` dataclass used as a simple DTO:
    - Fields: `id`, `start_date`, `end_date`, `type`, `status`, `reason`.

- **`app.py`**
  - **GET `/ess/leaves`**
    - Protected by `@token_required` (uses JWT `sub` = username).
    - Resolves logged-in `UserORM` and related `EmployeeORM`.
    - Loads all `LeaveRequestORM` rows for that employee, ordered by `StartDate` (desc).
    - Returns an array of leave objects:
      - `[{ id, startDate, endDate, type, status, reason }, ...]`
      - Dates are ISO strings `YYYY-MM-DD`.
  - **POST `/ess/leaves`**
    - Protected by `@token_required`.
    - Accepts JSON body:
      - `startDate` (ISO `YYYY-MM-DD`, required)
      - `endDate` (ISO `YYYY-MM-DD`, required)
      - `type` (required)
      - `reason` (optional)
    - Validations:
      - All required fields must be present.
      - `startDate` and `endDate` must be valid ISO dates.
      - `endDate` cannot be before `startDate`.
    - Persists a new `LeaveRequestORM` row:
      - `EmployeeId` from logged-in employee.
      - `Status = 'Pending'`.
    - Returns the created leave as JSON with HTTP `201 Created`.

## Frontend (SAP UI5)

Files in `workforce-portal/`.

### Routing

- **`manifest.json`**
  - Added new route and target:
    - Route `MyLeaves` with pattern `"leaves"`.
    - Target `MyLeaves` mapped to view `MyLeaves` (view level 4).

### Main Shell Updates

- **`webapp/view/Main.view.xml`**
  - Toolbar now has:
    - **My Profile** button → `press="onMyProfileButtonPress"`.
    - **My Leaves** button → `press="onMyLeavesButtonPress"`.
    - Refresh and Logout buttons unchanged (still call `onRefreshButtonPress`, `onLogoutButtonPress`).

- **`webapp/controller/Main.controller.js`**
  - New handlers:
    - `onMyProfileButtonPress()` → navigates to `"MyProfile"`.
    - `onMyLeavesButtonPress()` → navigates to `"MyLeaves"`.
  - Existing:
    - `onAfterRendering()` still calls `onRefreshButtonPress()` to validate the session.

### New ESS Screen: `MyLeaves`

- **`webapp/view/MyLeaves.view.xml`**
  - New XML view for **“My Leaves”**:
    - `Page` titled **My Leaves**.
    - Header button **“Request Leave”** → `press="onRequestLeaveButtonPress"`.
    - A responsive `Table` (`id="idItemsLeavesTable"`) bound to `leavesModel>/items`:
      - Columns: Start Date, End Date, Type, Status, Reason.
      - Rows show leave properties from the backend.
      - Status uses `ObjectStatus` with formatter to show color.
    - Toolbar button **Refresh** → `press="onRefreshButtonPress"`.

- **`webapp/controller/MyLeaves.controller.js`**
  - On init:
    - Creates a `JSONModel` named `leavesModel` with `items: []`.
    - Calls `loadLeaves()` to pull data from backend.
  - `formatStatusState(status)`:
    - Maps `Pending` → `Warning`, `Approved` → `Success`, `Rejected` → `Error`.
  - `ensureAuthenticated()`:
    - Reads JWT from `localStorage.authToken`.
    - If missing, redirects to the `Login` route.
  - `loadLeaves()`:
    - Calls `GET /api/ess/leaves` via `/api/ess/leaves` proxy URL.
    - On success, sets `leavesModel>/items` to the returned array.
  - **Request Leave dialog**:
    - `onRequestLeaveButtonPress()`:
      - Builds a `Dialog` with:
        - `DatePicker` for Start Date.
        - `DatePicker` for End Date.
        - `sap.m.Select` for Leave Type using `sap.ui.core.Item`:
          - Values: Annual, Sick, Casual, Unpaid.
        - `TextArea` for Reason (optional).
      - Submit button triggers `submitLeaveRequest(...)`.
    - `submitLeaveRequest(controls)`:
      - Validates that Start Date, End Date, and Leave Type are filled.
      - Converts JS dates to `YYYY-MM-DD` strings.
      - Sends `POST /api/ess/leaves` with `{ startDate, endDate, type, reason }`.
      - On success:
        - Closes dialog.
        - Shows `MessageToast` (“Leave request created.”).
        - Reloads the table via `loadLeaves()`.

