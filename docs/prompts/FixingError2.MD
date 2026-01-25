
Context: We are fixing three critical issues to complete the "Lead Capture -> Processing" pipeline.

1. **The Signal Mismatch:** The API signals the Parent Workflow (CEO), but the handler is buried in the Child (Manager). The workflow ignores the approval.
2. **The Data Gap:** The User Dashboard shows "Amount: $0" even after the user enters a loan amount in the funnel.
3. **The Missing PDF:** Because the signal fails, the `ProcessingWorkflow` (DocGen) never starts.

## Mission 1: Move the "Approval Gate" to the CEO (Backend)

**Target:** `backend/app/temporal/workflows/ceo.py` and `managers.py`

1. **Refactor `LeadCaptureWorkflow` (managers.py):**
   * **REMOVE** the `human_approval` signal handler.
   * **REMOVE** the `wait_condition`.
   * **Logic:** Run the AI analysis and return the result immediately. Return format: `{"recommendation": "APPROVED", "loan_data": ...}`.
2. **Refactor `LoanLifecycleWorkflow` (ceo.py):**
   * **ADD** state variable: `self.human_decision = None`.
   * **ADD** signal handler:
     ```python
     @workflow.signal
     def human_approval(self, decision: str):
         self.human_decision = decision
     ```
   * **Update `run` logic:**
     1. Execute `LeadCaptureWorkflow` (get the recommendation).
     2. **THE NEW GATE:** `await workflow.wait_condition(lambda: self.human_decision is not None)`
     3. **Transition:** If `self.human_decision == "APPROVED"`, start `ProcessingWorkflow` (passing the full `loan_data`).

## Mission 2: Fix the "Amount $0" Bug (API & DB)

**Target:** `backend/app/api/routes/applications.py`

1. **Update `create_application` endpoint:**
   * Ensure `loan_amount` from the request body is saved to the SQL database.
   * If using a JSON column (`loan_metadata`), ensure it is stored there.
   * If using a dedicated column, ensure it is mapped.
2. **Update `read_user_applications` endpoint:**
   * Ensure the response model includes the `loan_amount` fetched from the DB.

## Mission 3: Polish the User Dashboard (Frontend)

**Target:** `frontend/src/pages/UserDashboard.jsx`

1. **Enhance the Card/Table:**
   * Display **"Loan Amount"** formatted as currency (e.g., `$450,000`).
   * Add a **"Next Step"** indicator based on status (e.g., if Approved -> "Documents Sent").
   * Add a **"View Documents"** button (even if disabled for now) to show future intent.

## Execution

Generate the refactored code for `ceo.py`, `managers.py`, `applications.py`, and `UserDashboard.jsx`.
Ensure the Signal Handler is now on the Parent Workflow to fix the "Stuck" issue
