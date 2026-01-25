Read "backend/app/temporal/workflows/managers.py", "backend/app/temporal/workflows/ceo.py", "backend/app/api/routes/applications.py", and "frontend/src/pages/UserDashboard.jsx".

Context: We are finalizing the pipeline.

1. The "Gate" is fixed, but the AI Analysis is currently bypassed (stubbed). We need to restore it.
2. The Worker crashed due to `datetime.utcnow()`. We need to use `workflow.now()`.
3. We need to implement the "User Signature Loop" (User signs PDF -> Workflow advances).

## Mission 1: Re-Enable the "Brain" (Lead Capture)

**Target:** `backend/app/temporal/workflows/managers.py` (LeadCaptureWorkflow)

1. **Restore AI Analysis:**
   * In the `run` method, BEFORE returning, execute the `analyze_document` activity for the uploaded documents (Pay Stub, Tax Return).
   * **Logic:**
     * If AI confidence > 0.8 -> `ai_recommendation = "APPROVED"`
     * Else -> `ai_recommendation = "MANUAL_REVIEW"`
   * **Return:** Pass this calculated `ai_recommendation` back to the CEO.

## Mission 2: Fix the Time Crash (Safety)

**Target:** `backend/app/temporal/workflows/managers.py`

1. **Search & Replace:** Find `datetime.utcnow()` in the `_log` method (or anywhere else).
2. **Fix:** Replace with `workflow.now()`. (Import `workflow` from `temporalio`).

## Mission 3: The Signature Loop (Backend)

**Target:** `backend/app/api/routes/applications.py` and `ceo.py`

1. **API:** Create `POST /applications/{workflow_id}/sign`.
   * Locates the `Initial Disclosures.pdf`.
   * Creates a copy: `Initial Disclosures_SIGNED.pdf`.
   * Signals the CEO Workflow: `await handle.signal("borrower_signed", True)`.
2. **CEO Workflow (`LoanLifecycleWorkflow`):**
   * **After** `ProcessingWorkflow` completes (which generates the PDF):
   * **Update Status:** `self.current_stage = "WAITING_FOR_SIGNATURE"`.
   * **Wait:** `await workflow.wait_condition(lambda: self.borrower_signed is True)` (Add this state var).
   * **Transition:** Once signed, move to `UNDERWRITING`.

## Mission 4: The User Experience (Frontend)

**Target:** `frontend/src/pages/UserDashboard.jsx`

1. **Logic:** If status is "Waiting for Signature" (or similar):
   * Show a **"✍️ Sign Documents"** button.
   * Clicking it calls the `/sign` endpoint.
   * On success, refresh and show "Documents Signed".

## Execution

Generate the code to:

1. Restore `analyze_document` in managers.py.
2. Fix the `datetime` crash.
3. Implement the `/sign` endpoint and the CEO signature wait state.
4. Add the Sign button to the Dashboard.
