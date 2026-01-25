Context: Debugging "Silent Failure" where LeadCaptureWorkflow finishes too early.

## The Bug: Variable Collision

In `LeadCaptureWorkflow` (managers.py), the AI analysis likely sets `self.human_decision` (or `self.decision`) to "APPROVED".
This causes `await workflow.wait_condition(...)` to return immediately, skipping the manual approval step.

## Mission 1: Fix LeadCaptureWorkflow (managers.py)

Refactor the `run` method:

1. **Rename Variables:** Store the AI's result in `self.ai_recommendation`.
2. **Reset Decision:** Explicitly set `self.human_decision = None` at the start.
3. **The Gate:** Ensure the workflow waits specifically for the signal:
   `await workflow.wait_condition(lambda: self.human_decision is not None)`
4. **Return:** Return `self.human_decision` (The final authority).

## Mission 2: Verify The CEO (ceo.py)

Refactor `LoanLifecycleWorkflow` (or the main workflow class in this file):

1. **Transition Logic:** Check that when `LeadCaptureWorkflow` returns "APPROVED", it **immediately** calls `ProcessingWorkflow`.
2. **Data Passing:** Ensure the `loan_data` (including the new Loan Amount/Citizenship fields) is passed correctly from LeadCapture result into Processing inputs.

## Execution

Rewrite the `run` logic in `managers.py` to separate AI opinion from Human decision.
Verify the handoff logic in `ceo.py`.
