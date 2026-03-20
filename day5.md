# Day 5 — ESS Improvments (Details + Filter/Sort + Calendar View)

**Date:** 20-03-2026

## What I improved today

### Backend updates (`backend-flask/`)

1. **`GET /ess/leaves` now returns `createdAt`**
   - Added `createdAt` to each leave object so the frontend can:
     - sort by “Created At”
     - show leave details in a dialog.

2. **`POST /ess/leaves` and `PUT /ess/leaves/{id}/cancel` also include `createdAt` in the response**
   - Helps the UI keep the data consistent after create/cancel actions.

---

### Frontend updates (`workforce-portal/`)

1. **Leave details view (row click dialog)**
   - On the `MyLeaves` table, clicking a row opens a **Leave Details** dialog.
   - Dialog shows:
     - Leave ID
     - Start Date / End Date
     - Type
     - Status
     - Reason
     - Created At (now displayed in a readable date-time format instead of raw timestamp)

---

2. **Filtering & sorting (client-side)**
   - Added a **Filters** panel on `MyLeaves` with:
     - Status filter (`All`, `Pending`, `Approved`, `Rejected`, `Cancelled`)
     - Type filter (`All`, `Annual`, `Sick`, `Casual`, `Unpaid`)
     - Date range filter (`From`, `To`)
     - Sort (`Start newest`, `Start oldest`, `Created newest`)
   - Buttons:
     - **Apply** (updates the table)
     - **Clear** (resets filters to defaults)

---

3. **Calendar view (Fiori-compliant)**
   - Replaced the earlier date-based list view with a **Fiori-style Planning Calendar**.
   - Leaves are now displayed as visual blocks across their date range.
   - This provides a more intuitive and professional user experience.

   Improvements:
   - Better visualization of multi-day leaves
   - Status-based color indication (Approved, Pending, etc.)
   - Click interaction to view leave details

---

4. **UI5 stability fix (important)**
   - Fixed a runtime issue related to UI5 aggregation binding (`templateShareable`).
   - This ensures:
     - No duplicate ID errors
     - No memory leaks
     - Stable rendering of calendar appointments
     - Compatibility with future UI5 versions

---

5. **Date handling improvement**
   - Fixed raw ISO timestamp display issue (e.g., `2026-03-18T10:36:42...`)
   - Dates are now formatted into a user-friendly readable format in the UI.

