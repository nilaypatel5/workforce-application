# Day 4 — Polish ESS (Cancel + Validation)

**Date:** 18-03-2026

## Goal

Polish the ESS Leave Requests module so it is usable end-to-end:

- Employees can **request leave** with basic client-side validations.
- Employees can **cancel** their own leave requests **only while Pending**.

## Database Reference (unchanged)

Tables used:

- `Users`
- `Employees`
- `LeaveRequests`

`LeaveRequests` key fields used by the ESS module:

- `EmployeeId` → FK to `Employees(Id)` (ownership enforcement)
- `Status` default `'Pending'`
- `Reason` `NVARCHAR(500)` nullable
- `CreatedAt` `DATETIME2 DEFAULT SYSDATETIME()`

## Backend (Python / Flask)

File: `backend-flask/app.py`

### New endpoint: Cancel leave request

- **PUT `/ess/leaves/<id>/cancel`**
  - Protected route (`@token_required`).
  - Resolves the logged-in employee via JWT `sub` → `Users` → `Employees`.
  - Cancels **only** the leave request owned by that employee (`LeaveRequests.EmployeeId = Employees.Id`).
  - Business rule:
    - Only requests with **Status = `Pending`** can be cancelled.
  - On success:
    - Sets `Status = 'Cancelled'`
    - Returns the updated leave object:
      - `{ id, startDate, endDate, type, status, reason }`

## Frontend (SAP UI5)

Files in `workforce-portal/`.

### My Leaves table: Cancel action

File: `webapp/view/MyLeaves.view.xml`

- Added an **Action** column with a **Cancel** button.
- The Cancel button is only **visible for Pending** rows (status-driven visibility).

File: `webapp/controller/MyLeaves.controller.js`

- Added `isPendingStatus(status)` formatter to determine Pending rows.
- Added `onCancelLeaveButtonPress(event)`:
  - Reads the selected row context and leave `id`.
  - Shows a confirm dialog.
  - Calls `_cancelLeaveRequest(id)` on confirmation.
- Added `_cancelLeaveRequest(id)`:
  - Calls `PUT /api/ess/leaves/{id}/cancel`
  - Refreshes the table on success.

### Request Leave dialog: client-side validation improvements

File: `webapp/controller/MyLeaves.controller.js`

- Leave type selection:
  - Added a default “Select type” option with empty key.
  - Requires a valid type key before submit.
- Validations before `POST /api/ess/leaves`:
  - Start Date required
  - End Date required
  - Leave Type required
  - End Date cannot be before Start Date

### Status color mapping update

- `formatStatusState(status)` now also handles:
  - `Cancelled` / `Canceled` → `Information`

## Result

ESS Leave Requests module now supports:

- List leaves (`GET /api/ess/leaves`)
- Create leave request (`POST /api/ess/leaves`)
- Cancel pending leave request (`PUT /api/ess/leaves/{id}/cancel`)
- Frontend validations and a Cancel action for Pending items

