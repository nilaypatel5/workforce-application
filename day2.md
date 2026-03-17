# Day 2 — UI5 Frontend and ESS Profile API
**Date:** 17-03-2026

## Database Work (SSMS)
- Created a table: **Employees** with columns:
  - `Id` (INT, primary key, auto-increment)
  - `UserId` (INT, FK → `Users(Id)`, required)
  - `FirstName`, `LastName`, `Email` (required)
  - `Phone`, `Department` (optional)
  - `CreatedAt` (default current datetime)
- Inserted sample employee rows linked to existing `Users`

## Backend (Python / Flask)

Files are located in `backend-flask/`

### Employees model + mapping
- Added `EmployeeORM` mapping for the **Employees** table
- Added a profile response shape (`EmployeeProfile`)

### `GET /ess/profile`
- Created protected endpoint: `GET /ess/profile`
  - Requires `Authorization: Bearer <JWT>`
  - Uses the JWT subject (`sub`) to find the logged-in user
  - Fetches the employee record linked by `Employees.UserId`
  - Returns profile fields:
    - `firstName`, `lastName`, `email`, `phone`, `department`

### App port + CORS adjustments
- Backend server port is configurable via env var:
  - `PORT` (defaults to `5000`)
- CORS origins are configurable via:
  - `CORS_ORIGINS` (defaults to `http://localhost:8080`)

## Frontend (SAP UI5)

Files are located in `workforce-portal/`

### Project setup
- Created the UI5 frontend app: `workforce-portal/`
- Added UI5 tooling via `package.json`
  - Start command: `npm run start`

### Local dev proxy to backend
- Configured `ui5-middleware-simpleproxy` in `ui5.yaml`
  - Proxies `/api/*` → `http://127.0.0.1:5000`
  - This avoids CORS issues and keeps frontend requests relative (recommended for dev)

### Login flow
- Implemented login screen and controller:
  - Views/Controllers:
    - `webapp/view/Login.view.xml`
    - `webapp/controller/Login.controller.js`
  - `POST /api/auth/login`
  - Stores JWT in `localStorage` (`authToken`)

### Main shell page
- Implemented the main landing page after login:
  - Views/Controllers:
    - `webapp/view/Main.view.xml`
    - `webapp/controller/Main.controller.js`
  - Calls `GET /api/auth/me` to confirm the current session/token

### My Profile (ESS)
- Added a read-only My Profile page:
  - View: `webapp/view/MyProfile.view.xml`
  - Controller: `webapp/controller/MyProfile.controller.js`
- Controller loads profile on init:
  - Calls `GET /api/ess/profile` with Bearer token
  - Binds response data to a JSON model for display
