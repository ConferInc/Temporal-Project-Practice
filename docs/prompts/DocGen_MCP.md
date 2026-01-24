Context: The User Flow is confirmed (Funnel -> Login -> Process -> DocGen).
Gap: We need to collect Financial Data in the funnel to generate accurate docs later.

## Mission 1: Upgrade the Funnel (Frontend)

Target: `frontend/src/pages/BorrowerFunnel.jsx`

* **Expand the Wizard:** Add new steps between "Occupancy" and "Register":
  1. **Citizenship:** "Are you a U.S. Citizen or Permanent Resident?" (Yes/No).
  2. **Property Value:** Input field ($).
  3. **Down Payment:** Input field ($).
* **Logic:**
  * Calculate `Loan Amount` = `Property Value` - `Down Payment`.
  * Store these in the `initial_metadata` object passed to Registration.

## Mission 2: Build the DocGen MCP (Backend)

Target: `backend/app/temporal/activities/mcp_docgen.py`

* **Dependencies:** Ensure `fpdf2` is installed.
* **Templates (Knowledge Base):** Create a simple internal dictionary mapping:
  * `"Initial Disclosures"` -> Text containing placeholders `{name}`, `{loan_amount}`, `{rate}`, `{monthly_payment}`.
* **Function `generate_document`:**
  * Inputs: `doc_type`, `data` (dict), `config` (dict).
  * **Calculations:** If `monthly_payment` isn't provided, calculate a simple estimate (Rate: 6.5% Fixed, Term: 30yr) inside the MCP for the doc.
  * **Output:** Generate PDF -> Save to `uploads/{workflow_id}/` -> Return path.

## Mission 3: Wire the Processing Phase (Manager Logic)

Target: `backend/app/temporal/workflows/managers.py` (ProcessingWorkflow)

* **Update `run` method:**
  * **Step 1:** Extract `loan_amount` from the Application Data.
  * **Step 2:** Call `DocGenMCP.generate_document("Initial Disclosures", ...)` immediately upon entering Processing.
  * **Step 3:** Log the file generation so it appears in the Manager's "Audit Trail".

## Execution

1. Update `BorrowerFunnel.jsx` with the new inputs.
2. Create `mcp_docgen.py` with `fpdf2`.
3. Update `ProcessingWorkflow` to use this new tool.
