
## The Mission: Build the "Moxi Corp" Pyramid Architecture

We are moving from a flat workflow to a Hierarchical State Machine. You must implement the 3 Levels of the Pyramid: The CEO, The Managers, and The Workers.

## EXECUTION PLAN (Perform these 4 steps strictly in order)

### STEP 1: The Foundation (Data Models)

* **File:** `backend/app/models.py`
* **Action:**
  1. Create a Python Enum `LoanStage` with values: `LEAD_CAPTURE`, `PROCESSING`, `UNDERWRITING`, `CLOSING`, `ARCHIVED`.
  2. Update `Application` model: Add `loan_stage` (Enum, default=`LEAD_CAPTURE`) and `decision_reason` (Optional str).
  3. Create Pydantic models for Signals: `SignalApprove`, `SignalReject` (with reason).

### STEP 2: Level 3 - The Workers (MCP Activities)

* **Action:** Create a new directory `backend/app/temporal/activities/`.
* **File:** `backend/app/temporal/activities/mcp_comms.py`
  * Create class `CommsMCP`. Methods: `send_email(template_id, recipient)`, `send_sms`. (Mock implementation with `print` logs is fine for now).
* **File:** `backend/app/temporal/activities/mcp_encompass.py`
  * Create class `EncompassMCP`. Methods: `create_loan_file(data)`, `push_field_update(field_id, value)`.
* **File:** `backend/app/worker.py`
  * Register these new Activities with the Temporal Worker.

### STEP 3: Level 2 - The Department Managers (Child Workflows)

* **File:** `backend/app/temporal/workflows/managers.py`
* **Action:** Create two Child Workflows:
  1. `LeadCaptureWorkflow`:
     * Step 1: Execute `EncompassMCP.create_loan_file`.
     * Step 2: Execute `CommsMCP.send_email("Welcome")`.
     * Step 3: Wait for signal `HumanApproval`.
     * Returns: "APPROVED" or "REJECTED".
  2. `ProcessingWorkflow`:
     * (Placeholder) Logs "Started Processing Phase". Returns "COMPLETED".

### STEP 4: Level 1 - The CEO (Parent Workflow)

* **File:** `backend/app/temporal/workflows/ceo.py`
* **Action:** Create `LoanLifecycleWorkflow`.
* **Logic:**
  1. **Init:** Set state to `LEAD_CAPTURE`.
  2. **Phase 1:** Execute Child `LeadCaptureWorkflow`.
  3. **Check:** If Child returns "REJECTED", update DB state to `ARCHIVED` and End.
  4. **Transition:** If "APPROVED", update DB state to `PROCESSING`.
  5. **Phase 2:** Execute Child `ProcessingWorkflow`.
* **Queries:** Expose `get_current_stage()` to return the live status.

### Final Wiring

* Update `backend/app/main.py` to start `LoanLifecycleWorkflow` on `/apply`.

## Verification

After generating the code, verify that `worker.py` is correctly registering both the *New Workflows* and *New Activities*.
