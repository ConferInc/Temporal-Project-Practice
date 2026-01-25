/compact
Context: We are advancing to Phase 3: "Underwriting & Action".
Current State: User can "View Docs", but the "Sign" button is missing/broken. The CEO stops after Processing.

## Mission 1: The "Sign" Button (Frontend & API)

**Target:** `frontend/src/pages/ApplicantDashboard.jsx` and `backend/app/api/routes/applications.py`

1. **Frontend:**
   * Add a "Sign Disclosures" button next to "View Docs".
   * It should only be active if Status == "Documents Generated".
   * On Click: Call `POST /applications/{id}/sign`.
   * Show a "Signing..." spinner, then refresh to show "Status: Underwriting".
2. **API:**
   * Ensure the `/sign` endpoint:
     1. Creates `Initial_Disclosures_SIGNED.pdf`.
     2. Signals the CEO Workflow (`borrower_signature`, True).

## Mission 2: The Underwriting Manager (Backend)

**Target:** `backend/app/temporal/workflows/managers.py`

1. **Create `UnderwritingWorkflow` class:**
   * **Activity:** `verify_signature` (Mock: check if _SIGNED.pdf exists).
   * **Activity:** `evaluate_risk` (Logic: Check if Loan Amount < $1M and Credit Score > 700).
   * **Return:** "CLEAR_TO_CLOSE" or "REFER_TO_HUMAN".

## Mission 3: The CEO Orchestration (Backend)

**Target:** `backend/app/temporal/workflows/ceo.py`

1. **Update `LoanLifecycleWorkflow`:**
   * **State:** After `ProcessingWorkflow` finishes, set stage to `WAITING_FOR_SIGNATURE`.
   * **Gate:** `await workflow.wait_condition(lambda: self.borrower_signed)`
   * **Next Step:** Once signed, execute `UnderwritingWorkflow`.
   * **Final Transition:** If Underwriting says "CLEAR_TO_CLOSE", update status to "Closing".

## Execution

Generate the code to:

1. Fix the Frontend Signing UI.
2. Implement the API endpoint for signing.
3. Build the `UnderwritingWorkflow`.
4. Connect the CEO to this new phase.



/compact
Context: The Backend logic is solid, but the Frontend looks basic.
Goal: Create a "Mission Control" aesthetic for the Manager and a "Guided Journey" for the User.
Integrate this with the new "Underwriting" phase logic.

## Theme: "Automation Transparency"

The Manager Dashboard should look like a cockpit.

* **Live Feed:** A scrolling log of actions ("AI Agent analyzing...", "DocGen creating PDF...").
* **Worker Status:** Indicators showing if our Agents (AI, Encompass, DocGen) are Active or Idle.
* **Data Presentation:** No more boring input fields. Use "Data Cards" with confidence scores and "Source" badges.

## Mission 1: The "Mission Control" Layout (Manager)

**Target:** `frontend/src/pages/ManagerDashboard.jsx` and `components/Layout.jsx`

1. **Sidebar Navigation:** Add a professional sidebar: "Dashboard", "Active Loans", "System Health", "Settings".
2. **Live Activity Stream:**
   * Create a `SystemLogs` component.
   * Poll `GET /applications/recent_logs` (Need to create this) every 2s.
   * Visual: Terminal-like look (black background, green/blue text) showing the last 5 system events across ALL loans.
3. **Worker Status Widget:**
   * Visual indicators: "AI Analyst: 🟢 Online", "DocGen: 🟢 Processing".
   * (Mock logic is fine for now, or check queue depth if possible).

## Mission 2: The "Application Detail" Overhaul (Manager)

**Target:** `frontend/src/pages/ApplicationDetail.jsx`

1. **Visual Hierarchy:**
   * **Header:** Big status badge, Loan Amount, "Clear to Close" progress bar.
   * **Left Column (The Input):** Thumbnail previews of the PDF documents.
   * **Middle Column (The Brain):** The AI Analysis.
     * NOT input fields. Use **Info Cards**.
     * Example: "Income: $120,000" (Badge: "Verified by Tax Return").
     * If Mismatch -> Show Red alert box.
   * **Right Column (The Action):** "Approve", "Reject", "Request Info".

## Mission 3: The "Guided Journey" (User Dashboard)

**Target:** `frontend/src/pages/ApplicantDashboard.jsx`

1. **Progress Stepper:** A visual timeline at the top:
   * `Applied` -> `AI Review` -> `Manager Approved` -> `Sign Docs` -> `Underwriting` -> `Funded`.
2. **Action Cards:**
   * If status is "Waiting for Signature", show a big card: "Action Required" with the Sign button.

## Mission 4: The Underwriting Logic (Backend Integration)

**Target:** `backend/app/temporal/workflows/managers.py` & `ceo.py`

1. **Implement `UnderwritingWorkflow`:**
   * Triggered after User Signs.
   * **Logic:** Verify Signature -> Check DTI (Mock) -> Move to "Closing".
2. **Update API:** Ensure `/sign` triggers this workflow.

## Execution

1. Revamp the UI components to be "Professional & Data-Dense".
2. Implement the "Live Logs" API and component.
3. Connect the Underwriting backend logic.
