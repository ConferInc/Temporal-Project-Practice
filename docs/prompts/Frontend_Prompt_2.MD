/compact
Read "docs/protocols/1_ARCHITECT.md".
Context: Major UI/UX Overhaul. We are pivoting the Manager Dashboard to an "Encompass-style" LOS Workspace.

## Mission 1: The Backend (Data Mutation)
Target: `backend/app/temporal/workflows/managers.py` (LeadCaptureWorkflow)
1.  **Add State Variable:** `self.loan_data` (Initialize with input args).
2.  **Add Signal:** `update_field(field_name: str, value: Any)`.
    * Logic: Update `self.loan_data[field_name] = value`.
    * Log: "Manager updated {field_name} to {value}".
3.  **Update Query:** `get_loan_data` should return the *current* (potentially modified) data.

## Mission 2: The API (Wiring)
Target: `backend/app/api/routes/applications.py`
1.  **New Endpoint:** `PATCH /applications/{workflow_id}/fields`
    * Accepts `{field: str, value: any}`.
    * Sends the `update_field` signal to the running workflow.
    * Updates the SQL Database `loan_metadata` column to match.

## Mission 3: The Frontend (The Encompass Workspace)
Target: `frontend/src/pages/ManagerDashboard.jsx` and `ApplicationDetail.jsx`
1.  **Layout:** Create a "Sidebar + Main Content" layout.
    * **Sidebar:** "Pipeline View" (Lead Capture, Processing, etc.).
    * **Main:** The "Loan File".
2.  **The Loan File UI:**
    * **Header:** Loan Number, Borrower Name, Current Stage badge.
    * **Tabs:**
        * **[Forms]:** A grid of inputs (Income, SSN, Citizenship). *Making changes here calls the PATCH endpoint.*
        * **[eFolder]:** List of uploaded documents with "View" buttons (opens PDF in new tab) and Status badges.
        * **[Log]:** The Temporal Audit Trail.
3.  **Action Bar:** Floating bottom bar with "✅ Approve" and "❌ Reject" buttons.

## Style Guide
* Use a "Dense" design (smaller padding, borders) to mimic professional software.
* Use `lucide-react` icons: `FolderOpen`, `FileText`, `CheckSquare`, `History`.