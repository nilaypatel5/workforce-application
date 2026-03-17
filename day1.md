# Day 1 — Quick Notes (Backend API + SSMS)
**Date:** 16-03-2026

## Database Work (SSMS)
- Created a database: **EmployeeAuth**
- Created a table: **Users** with columns:  
  - `Id` (INT, primary key, auto-increment)  
  - `Username` (NVARCHAR(50), unique, required)  
  - `HashedPassword` (NVARCHAR(255), required)  
  - `IsActive` (BIT, default 1)  
- Inserted sample users:  
  - `employee1`  
  - `employee2`  
  - `employee3`  
  - `employee4`
- Checked data using:  
```sql
USE EmployeeAuth;
SELECT * FROM Users;
````

## Backend (Python / Flask)

Files are located in `backend-flask/`

### `app.py`

* Runs the Flask API
* Enables CORS for UI at `http://localhost:8080`
* Provides endpoints:

  * `GET /` → health check
  * `POST /auth/login` → login and returns JWT
  * `GET /auth/me` → protected route (requires Bearer token)

### `auth_service.py`

* Communicates with the Users table to authenticate users
* Automatically upgrades plain-text passwords to bcrypt after a successful login
* Creates JWT tokens for authenticated users

### `models.py`

* Sets up SQLAlchemy
* Maps **Users** table to `UserORM`
* Includes a simple `User` dataclass

### `config.py`

* Stores settings:

  * JWT secret key
  * SQL Server connection string to **EmployeeAuth**

### `security.py`

* Handles password hashing and verification (bcrypt)
* Creates JWT tokens with expiry and subject

### Test / Utility Scripts

* `testdb.py` → tests SQL Server connection using `SELECT 1`
* `test_auth.py` → tests login for `employee1` and prints the JWT
* `hash_users.py` → one-time script to hash all existing plain-text passwords in Users

