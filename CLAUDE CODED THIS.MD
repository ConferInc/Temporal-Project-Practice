 @temporal/workflows/ceo.py
  @temporal/workflows/managers.py

  We are refactoring the CEO Workflow (LoanLifecycleWorkflow) to use the "Waiter Pattern" for the human approval gate.

  Current Architecture:
  The system uses a "Pyramid" structure where the CEO orchestrates Manager workflows. Currently, the CEO workflow handles approval linearly.

  Goal:
  Refactor `LoanLifecycleWorkflow` in `temporal/workflows/ceo.py` to use Temporal Signals and `wait_condition` for the underwriting decision.

  Requirements:
  1. Define State: Add class-level state variables to `LoanLifecycleWorkflow`:
  - `self.is_underwriting_complete = False`
  - `self.underwriting_decision = None` (approved/rejected)

  2. Create Signal: Define a `@workflow.signal` method named `submit_underwriting_decision(approved: bool, reason: str)`.
  - This method should update the state variables above.

  3. Implement the Wait:
  - In the main `run` method, after the "Processing" manager completes, insert a `workflow.wait_condition`.
  - It should block execution until `self.is_underwriting_complete` becomes True.
  - Set a timeout (e.g., 7 days) for this wait condition to handle abandoned applications.

  4. Logic Flow Update:
  - If the signal is "Approved": Proceed to execute the "Closing" manager workflow.
  - If the signal is "Rejected": Log the rejection and end the workflow (do not proceed to Closing).
  - If timed out: Treat as rejected/withdrawn.

  Constraints:
  - Keep the existing `Manager` workflow calls (`LeadCaptureWorkflow`, `ProcessingWorkflow`).
  - Do not modify the Manager workflows yet, only the CEO orchestration logic.
  - Ensure all imports (like `timedelta`) are handled correctly inside `workflow.unsafe.imports_passed_through()` if necessary.

● I'll read the current CEO workflow to understand its structure before making the refactoring changes.

● Read 2 files (ctrl+o to expand)

● Now I understand the current structure. I can see that self.underwriting_decision already exists but is used to store the automated UnderwritingWorkflow result. I'll need to rename that to avoid conflict with
   the new human underwriting decision signal.

  Let me implement the "Waiter Pattern" for the human underwriting decision gate:

● Update(backend\app\temporal\workflows\ceo.py)
  ⎿  Added 10 lines, removed 2 lines
      44          self.loan_data = {}  # Stores current loan data for field updates
      45          # Signature Loop: Track borrower signature
      46          self.borrower_signed = False
      47 -        # Underwriting result
      48 -        self.underwriting_decision = None
      47 +
      48 +        # =========================================
      49 +        # Underwriting Waiter Pattern State
      50 +        # =========================================
      51 +        self.is_underwriting_complete = False
      52 +        self.underwriting_decision = None  # "approved" or "rejected"
      53 +        self.underwriting_decision_reason = None
      54 +
      55 +        # Automated underwriting result (from UnderwritingWorkflow)
      56 +        self.automated_uw_decision = None
      57          self.risk_evaluation = {}
      58
      59      def _add_log(self, agent: str, message: str):

● Update(backend\app\temporal\workflows\ceo.py)
  ⎿  Added 15 lines
      101          self.borrower_signed = signed
      102          workflow.logger.info(f"CEO received borrower signature: {signed}")
      103
      104 +    @workflow.signal
      105 +    def submit_underwriting_decision(self, approved: bool, reason: str):
      106 +        """
      107 +        Signal handler for human underwriting decision (Waiter Pattern).
      108 +        Called when an underwriter approves or rejects the loan application.
      109 +
      110 +        Args:
      111 +            approved: True if loan is approved, False if rejected
      112 +            reason: Explanation for the decision
      113 +        """
      114 +        self.underwriting_decision = "approved" if approved else "rejected"
      115 +        self.underwriting_decision_reason = reason
      116 +        self.is_underwriting_complete = True
      117 +        workflow.logger.info(f"CEO received underwriting decision: {self.underwriting_decision} - {reason}")
      118 +
      119      # =========================================
      120      # Queries - Expose live status
      121      # =========================================

● Now I'll add the wait_condition after Processing completes with a 7-day timeout, and update the logic flow:

● Update(backend\app\temporal\workflows\ceo.py)
  ⎿  Added 67 lines
      233          self._add_log("Processing", f"Phase completed: {processing_result}")
      234
      235          # =========================================
      236 +        # Underwriting Decision Gate (Waiter Pattern)
      237 +        # Wait for human underwriter to approve/reject the application
      238 +        # =========================================
      239 +        self.current_stage = LoanStage.UNDERWRITING
      240 +        self._add_log("CEO", "Waiting for underwriting decision...")
      241 +
      242 +        await workflow.execute_activity(
      243 +            update_loan_metadata,
      244 +            args=[workflow.info().workflow_id, {
      245 +                "status": "Pending Underwriting Decision",
      246 +                "loan_stage": LoanStage.UNDERWRITING.value
      247 +            }],
      248 +            start_to_close_timeout=timedelta(seconds=30)
      249 +        )
      250 +
      251 +        workflow.logger.info("CEO: Waiting for underwriting decision signal (7-day timeout)...")
      252 +
      253 +        # Wait for underwriting decision with 7-day timeout
      254 +        underwriting_wait_result = await workflow.wait_condition(
      255 +            lambda: self.is_underwriting_complete,
      256 +            timeout=timedelta(days=7)
      257 +        )
      258 +
      259 +        # Handle timeout (wait_condition returns False if timed out)
      260 +        if not underwriting_wait_result:
      261 +            workflow.logger.warning("CEO: Underwriting decision timed out after 7 days")
      262 +            self._add_log("CEO", "Underwriting decision TIMED OUT - Application withdrawn")
      263 +            self.current_stage = LoanStage.ARCHIVED
      264 +            self.decision_reason = "Underwriting decision timed out - application withdrawn"
      265 +
      266 +            await workflow.execute_activity(
      267 +                update_loan_metadata,
      268 +                args=[workflow.info().workflow_id, {
      269 +                    "status": "Withdrawn (Timeout)",
      270 +                    "loan_stage": LoanStage.ARCHIVED.value,
      271 +                    "final_status": "WITHDRAWN"
      272 +                }],
      273 +                start_to_close_timeout=timedelta(seconds=30)
      274 +            )
      275 +
      276 +            return "WITHDRAWN"
      277 +
      278 +        workflow.logger.info(f"CEO received underwriting decision: {self.underwriting_decision}")
      279 +        self._add_log("Underwriter", f"Decision: {self.underwriting_decision.upper()} - {self.underwriting_decision_reason}")
      280 +
      281 +        # Check: If rejected, archive and end
      282 +        if self.underwriting_decision == "rejected":
      283 +            self.current_stage = LoanStage.ARCHIVED
      284 +            self.decision_reason = f"Rejected by underwriter: {self.underwriting_decision_reason}"
      285 +            self._add_log("CEO", "Application REJECTED by underwriter - Moving to Archive")
      286 +
      287 +            await workflow.execute_activity(
      288 +                update_loan_metadata,
      289 +                args=[workflow.info().workflow_id, {
      290 +                    "status": "Rejected by Underwriter",
      291 +                    "loan_stage": LoanStage.ARCHIVED.value,
      292 +                    "final_status": "REJECTED",
      293 +                    "rejection_reason": self.underwriting_decision_reason
      294 +                }],
      295 +                start_to_close_timeout=timedelta(seconds=30)
      296 +            )
      297 +
      298 +            return "REJECTED"
      299 +
      300 +        self._add_log("CEO", "Underwriting APPROVED - Proceeding to signature and closing")
      301 +
      302 +        # =========================================
      303          # Signature Gate: Wait for Borrower to Sign Disclosures
      304          # =========================================
      305          self.current_stage = LoanStage.UNDERWRITING  # Reusing UNDERWRITING as "Waiting for Signature"

● Now I need to update the existing code that uses self.underwriting_decision for the automated UnderwritingWorkflow result to use self.automated_uw_decision instead:

● Update(backend\app\temporal\workflows\ceo.py)
  ⎿  Added 3 lines, removed 3 lines
      343              retry_policy=RetryPolicy(maximum_attempts=1)
      344          )
      345
      346 -        self.underwriting_decision = underwriting_result.get("decision", "REFER_TO_HUMAN")
      346 +        self.automated_uw_decision = underwriting_result.get("decision", "REFER_TO_HUMAN")
      347          self.risk_evaluation = underwriting_result.get("risk_evaluation", {})
      348
      349 -        workflow.logger.info(f"Underwriting completed with decision: {self.underwriting_decision}")
      350 -        self._add_log("Underwriting", f"Decision: {self.underwriting_decision}")
      349 +        workflow.logger.info(f"Underwriting completed with decision: {self.automated_uw_decision}")
      350 +        self._add_log("Underwriting", f"Decision: {self.automated_uw_decision}")
      351
      352          # Persist underwriting results to SQL (including status update)
      353          await workflow.execute_activity(

● Update(backend\app\temporal\workflows\ceo.py)
  ⎿  Added 3 lines, removed 3 lines
      353          await workflow.execute_activity(
      354              update_loan_metadata,
      355              args=[workflow.info().workflow_id, {
      356 -                "underwriting_decision": self.underwriting_decision,
      356 +                "underwriting_decision": self.automated_uw_decision,
      357                  "risk_evaluation": self.risk_evaluation,
      358                  "status": "Underwriting Complete"
      359              }],
      360              start_to_close_timeout=timedelta(seconds=30)
      361          )
      362
      363 -        # Check underwriting decision
      364 -        if self.underwriting_decision == "REFER_TO_HUMAN":
      363 +        # Check automated underwriting decision
      364 +        if self.automated_uw_decision == "REFER_TO_HUMAN":
      365              self._add_log("CEO", "Underwriting referred for additional human review")
      366              # For now, we'll still proceed to closing but mark for review
      367              # In production, might wait for another human gate here

● Update(backend\app\temporal\workflows\ceo.py)
  ⎿  Added 2 lines, removed 2 lines
      369          # =========================================
      370          # Phase 4: Closing
      371          # =========================================
      372 -        if self.underwriting_decision == "CLEAR_TO_CLOSE":
      372 +        if self.automated_uw_decision == "CLEAR_TO_CLOSE":
      373              self.current_stage = LoanStage.CLOSING
      374              self._add_log("CEO", "CLEAR TO CLOSE - Moving to closing phase")
      375              workflow.logger.info("CEO: Loan is Clear to Close!")
     ...
      382          await workflow.execute_activity(
      383              update_loan_metadata,
      384              args=[workflow.info().workflow_id, {
      385 -                "status": "Clear to Close" if self.underwriting_decision == "CLEAR_TO_CLOSE" else "Closing with Conditions",
      385 +                "status": "Clear to Close" if self.automated_uw_decision == "CLEAR_TO_CLOSE" else "Closing with Conditions",
      386                  "loan_stage": LoanStage.CLOSING.value
      387              }],
      388              start_to_close_timeout=timedelta(seconds=30)

● Update(backend\app\temporal\workflows\ceo.py)
  ⎿  Added 1 line, removed 1 line
      446                  "status": "Funded",
      447                  "loan_stage": LoanStage.ARCHIVED.value,
      448                  "final_status": "COMPLETED",
      449 -                "underwriting_decision": self.underwriting_decision
      449 +                "underwriting_decision": self.automated_uw_decision
      450              }],
      451              start_to_close_timeout=timedelta(seconds=30)
      452          )

● Let me also update the signature gate section since we now enter UNDERWRITING stage earlier for the decision gate. I'll read the current state to verify all changes are correct:

● Read 1 file (ctrl+o to expand)

● The refactoring is complete. Let me also add a query method to expose the underwriting decision state for the frontend:

● Update(backend\app\temporal\workflows\ceo.py)
  ⎿  Added 10 lines
      140          """Query the audit log"""
      141          return self.logs
      142
      143 +    @workflow.query
      144 +    def get_underwriting_status(self) -> dict:
      145 +        """Query the underwriting decision status (Waiter Pattern)"""
      146 +        return {
      147 +            "is_complete": self.is_underwriting_complete,
      148 +            "decision": self.underwriting_decision,
      149 +            "reason": self.underwriting_decision_reason,
      150 +            "automated_decision": self.automated_uw_decision
      151 +        }
      152 +
      153      # =========================================
      154      # Main Workflow Execution
      155      # =========================================

● The refactoring is complete. Here's a summary of the changes made to ceo.py:

  Changes Summary

  1. State Variables Added (lines 48-57)

  # Underwriting Waiter Pattern State
  self.is_underwriting_complete = False
  self.underwriting_decision = None  # "approved" or "rejected"
  self.underwriting_decision_reason = None

  # Automated underwriting result (from UnderwritingWorkflow)
  self.automated_uw_decision = None  # renamed from underwriting_decision

  2. New Signal Handler (lines 104-117)

  @workflow.signal
  def submit_underwriting_decision(self, approved: bool, reason: str):
      """Signal handler for human underwriting decision (Waiter Pattern)."""
      self.underwriting_decision = "approved" if approved else "rejected"
      self.underwriting_decision_reason = reason
      self.is_underwriting_complete = True

  3. New Query Method (lines 143-151)

  @workflow.query
  def get_underwriting_status(self) -> dict:
      """Query the underwriting decision status (Waiter Pattern)"""

  4. Waiter Pattern Implementation (lines 235-300)

  After Processing completes:
  - Sets stage to UNDERWRITING and updates SQL status to "Pending Underwriting Decision"
  - Waits for submit_underwriting_decision signal with 7-day timeout
  - If timeout: Returns "WITHDRAWN" and archives the application
  - If rejected: Returns "REJECTED" with reason and archives
  - If approved: Proceeds to signature gate and closing

  Updated Flow

  LEAD_CAPTURE → (human_approval) → PROCESSING → (submit_underwriting_decision) →
      SIGNATURE → UnderwritingWorkflow → CLOSING → ARCHIVED
                           ↓ (rejected/timeout)
                        ARCHIVED