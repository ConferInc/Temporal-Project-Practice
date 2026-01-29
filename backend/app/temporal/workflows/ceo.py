"""
Pyramid Architecture: Level 1 - The CEO (Parent Workflow)

The LoanLifecycleWorkflow is the supreme orchestrator that manages
the entire loan lifecycle by delegating to Department Manager workflows.

State Machine:
LEAD_CAPTURE → PROCESSING → UNDERWRITING → CLOSING → ARCHIVED
                    ↓ (if rejected)
                 ARCHIVED
"""
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

# Import child workflows
with workflow.unsafe.imports_passed_through():
    from app.models.sql import LoanStage
    from .managers import LeadCaptureWorkflow, ProcessingWorkflow, UnderwritingWorkflow
    from app.temporal.activities.mcp_encompass import update_loan_metadata
    from app.temporal.activities.mcp_docgen import generate_document
    from app.temporal.activities.mcp_comms import send_email


@workflow.defn
class LoanLifecycleWorkflow:
    """
    Level 1 CEO: The Supreme Orchestrator

    Manages the entire loan lifecycle by:
    1. Tracking the current loan stage
    2. Delegating to child workflows for each phase
    3. Handling transitions and rejections
    4. Exposing queries for real-time status
    """

    def __init__(self) -> None:
        self.current_stage = LoanStage.LEAD_CAPTURE
        self.decision_reason = None
        self.loan_number = None
        self.logs = []
        # THE GATE: Human decision is tracked at CEO level
        self.human_decision = None
        self.loan_data = {}  # Stores current loan data for field updates
        # Signature Loop: Track borrower signature
        self.borrower_signed = False

        # =========================================
        # Underwriting Waiter Pattern State
        # =========================================
        self.is_underwriting_complete = False
        self.underwriting_decision = None  # "approved" or "rejected"
        self.underwriting_decision_reason = None

        # Automated underwriting result (from UnderwritingWorkflow)
        self.automated_uw_decision = None
        self.risk_evaluation = {}

    def _add_log(self, agent: str, message: str):
        """Add an audit log entry"""
        entry = {
            "agent": agent,
            "message": message,
            "timestamp": workflow.now().isoformat(),
            "stage": self.current_stage.value
        }
        self.logs.append(entry)

    # =========================================
    # Signals - Human approval gate at CEO level
    # =========================================

    @workflow.signal
    def human_approval(self, approved: bool):
        """
        Signal handler for human manager approval.
        THE GATE: This is where human decisions are received.
        """
        self.human_decision = "APPROVED" if approved else "REJECTED"
        workflow.logger.info(f"CEO received human decision: {self.human_decision}")

    @workflow.signal
    def update_field(self, field_name: str, value):
        """Signal handler for real-time field updates from manager dashboard"""
        if "applicant_info" not in self.loan_data:
            self.loan_data["applicant_info"] = {}

        # Handle nested applicant_info fields
        if field_name in ["name", "email", "ssn", "stated_income"]:
            self.loan_data["applicant_info"][field_name] = value
        else:
            self.loan_data[field_name] = value
        workflow.logger.info(f"CEO: Manager updated {field_name} to {value}")

    @workflow.signal
    def borrower_signature(self, signed: bool):
        """
        Signal handler for borrower document signature.
        Called when borrower signs Initial Disclosures.
        """
        self.borrower_signed = signed
        workflow.logger.info(f"CEO received borrower signature: {signed}")

    @workflow.signal
    def submit_underwriting_decision(self, approved: bool, reason: str):
        """
        Signal handler for human underwriting decision (Waiter Pattern).
        Called when an underwriter approves or rejects the loan application.

        Args:
            approved: True if loan is approved, False if rejected
            reason: Explanation for the decision
        """
        self.underwriting_decision = "approved" if approved else "rejected"
        self.underwriting_decision_reason = reason
        self.is_underwriting_complete = True
        workflow.logger.info(f"CEO received underwriting decision: {self.underwriting_decision} - {reason}")

    # =========================================
    # Queries - Expose live status
    # =========================================

    @workflow.query
    def get_current_stage(self) -> str:
        """Query the current loan stage"""
        return self.current_stage.value

    @workflow.query
    def get_loan_number(self) -> str:
        """Query the Encompass loan number"""
        return self.loan_number

    @workflow.query
    def get_decision_reason(self) -> str:
        """Query the decision reason (if rejected)"""
        return self.decision_reason

    @workflow.query
    def get_logs(self) -> list:
        """Query the audit log"""
        return self.logs

    @workflow.query
    def get_underwriting_status(self) -> dict:
        """Query the underwriting decision status (Waiter Pattern)"""
        return {
            "is_complete": self.is_underwriting_complete,
            "decision": self.underwriting_decision,
            "reason": self.underwriting_decision_reason,
            "automated_decision": self.automated_uw_decision
        }

    # =========================================
    # Main Workflow Execution
    # =========================================

    @workflow.run
    async def run(self, input_data: dict) -> str:
        """
        Execute the complete loan lifecycle.

        Args:
            input_data: Dict containing applicant_info, file_paths, etc.

        Returns:
            Final status: "APPROVED", "REJECTED", or "COMPLETED"
        """
        applicant_name = input_data.get("applicant_info", {}).get("name", "Unknown")
        workflow.logger.info(f"CEO Workflow started for {applicant_name}")
        self._add_log("CEO", f"Loan lifecycle initiated for {applicant_name}")

        # =========================================
        # Phase 1: Lead Capture
        # =========================================
        self.current_stage = LoanStage.LEAD_CAPTURE
        self._add_log("CEO", "Delegating to Lead Capture Department")

        lead_capture_result = await workflow.execute_child_workflow(
            LeadCaptureWorkflow.run,
            args=[input_data],
            id=f"{workflow.info().workflow_id}-lead-capture",
            retry_policy=RetryPolicy(maximum_attempts=1)
        )

        # Extract recommendation and loan_data from LeadCapture result
        ai_recommendation = lead_capture_result.get("recommendation", "PENDING_REVIEW")
        self.loan_data = lead_capture_result.get("loan_data", input_data)
        self.loan_number = lead_capture_result.get("loan_number")
        analysis_result = lead_capture_result.get("analysis", {})

        workflow.logger.info(f"Lead Capture completed with AI recommendation: {ai_recommendation}")
        self._add_log("Lead Capture", f"Phase completed. AI Recommendation: {ai_recommendation}")

        # Persist analysis results to SQL for frontend display
        if analysis_result:
            metadata_update = {
                "analysis": analysis_result,
                "ai_recommendation": ai_recommendation,
                "loan_number": self.loan_number
            }
            await workflow.execute_activity(
                update_loan_metadata,
                args=[workflow.info().workflow_id, metadata_update],
                start_to_close_timeout=timedelta(seconds=30)
            )
            workflow.logger.info("Analysis results persisted to SQL")
            self._add_log("CEO", f"AI Analysis: verified_income=${analysis_result.get('verified_income', 0):,}, mismatch={analysis_result.get('income_mismatch', False)}")

        self._add_log("CEO", "Waiting for human approval...")

        # =========================================
        # THE GATE: Wait for human approval signal
        # This is the ONLY place where we wait for human decision
        # =========================================
        workflow.logger.info("CEO: Waiting for human approval signal...")
        await workflow.wait_condition(lambda: self.human_decision is not None)

        workflow.logger.info(f"CEO received human decision: {self.human_decision}")
        self._add_log("Human Manager", f"Decision: {self.human_decision}")

        # Check: If rejected, archive and end
        if self.human_decision == "REJECTED":
            self.current_stage = LoanStage.ARCHIVED
            self.decision_reason = "Rejected by human manager"
            self._add_log("CEO", "Application REJECTED - Moving to Archive")
            return "REJECTED"

        # =========================================
        # Phase 2: Processing (Transition on Approval)
        # Pass the loan_data (includes any manager field updates)
        # =========================================
        self.current_stage = LoanStage.PROCESSING
        self._add_log("CEO", "Human APPROVED - Delegating to Processing Department")

        processing_result = await workflow.execute_child_workflow(
            ProcessingWorkflow.run,
            args=[self.loan_data],  # Pass current loan_data with any updates
            id=f"{workflow.info().workflow_id}-processing",
            retry_policy=RetryPolicy(maximum_attempts=1)
        )

        workflow.logger.info(f"Processing completed with: {processing_result}")
        self._add_log("Processing", f"Phase completed: {processing_result}")

        # =========================================
        # Underwriting Decision Gate (Waiter Pattern)
        # Wait for human underwriter to approve/reject the application
        # =========================================
        self.current_stage = LoanStage.UNDERWRITING
        self._add_log("CEO", "Waiting for underwriting decision...")

        await workflow.execute_activity(
            update_loan_metadata,
            args=[workflow.info().workflow_id, {
                "status": "Pending Underwriting Decision",
                "loan_stage": LoanStage.UNDERWRITING.value
            }],
            start_to_close_timeout=timedelta(seconds=30)
        )

        workflow.logger.info("CEO: Waiting for underwriting decision signal (7-day timeout)...")

        # Wait for underwriting decision with 7-day timeout
        underwriting_wait_result = await workflow.wait_condition(
            lambda: self.is_underwriting_complete,
            timeout=timedelta(days=7)
        )

        # Handle timeout (wait_condition returns False if timed out)
        if not underwriting_wait_result:
            workflow.logger.warning("CEO: Underwriting decision timed out after 7 days")
            self._add_log("CEO", "Underwriting decision TIMED OUT - Application withdrawn")
            self.current_stage = LoanStage.ARCHIVED
            self.decision_reason = "Underwriting decision timed out - application withdrawn"

            await workflow.execute_activity(
                update_loan_metadata,
                args=[workflow.info().workflow_id, {
                    "status": "Withdrawn (Timeout)",
                    "loan_stage": LoanStage.ARCHIVED.value,
                    "final_status": "WITHDRAWN"
                }],
                start_to_close_timeout=timedelta(seconds=30)
            )

            return "WITHDRAWN"

        workflow.logger.info(f"CEO received underwriting decision: {self.underwriting_decision}")
        self._add_log("Underwriter", f"Decision: {self.underwriting_decision.upper()} - {self.underwriting_decision_reason}")

        # Check: If rejected, archive and end
        if self.underwriting_decision == "rejected":
            self.current_stage = LoanStage.ARCHIVED
            self.decision_reason = f"Rejected by underwriter: {self.underwriting_decision_reason}"
            self._add_log("CEO", "Application REJECTED by underwriter - Moving to Archive")

            await workflow.execute_activity(
                update_loan_metadata,
                args=[workflow.info().workflow_id, {
                    "status": "Rejected by Underwriter",
                    "loan_stage": LoanStage.ARCHIVED.value,
                    "final_status": "REJECTED",
                    "rejection_reason": self.underwriting_decision_reason
                }],
                start_to_close_timeout=timedelta(seconds=30)
            )

            return "REJECTED"

        self._add_log("CEO", "Underwriting APPROVED - Proceeding to signature and closing")

        # =========================================
        # Signature Gate: Wait for Borrower to Sign Disclosures
        # =========================================
        self.current_stage = LoanStage.UNDERWRITING  # Reusing UNDERWRITING as "Waiting for Signature"
        self._add_log("CEO", "Initial Disclosures generated - Waiting for borrower signature")

        # Update SQL status AND loan_stage to show waiting for signature
        # CRITICAL: These special keys are extracted by update_loan_metadata and written to SQL columns
        await workflow.execute_activity(
            update_loan_metadata,
            args=[workflow.info().workflow_id, {
                "status": "Waiting for Signature",
                "loan_stage": LoanStage.UNDERWRITING.value
            }],
            start_to_close_timeout=timedelta(seconds=30)
        )

        workflow.logger.info("CEO: Waiting for borrower signature...")

        await workflow.wait_condition(lambda: self.borrower_signed is True)

        workflow.logger.info("CEO: Borrower signature received!")
        self._add_log("Borrower", "Documents signed by borrower")

        # =========================================
        # Phase 3: Underwriting - Execute UnderwritingWorkflow
        # =========================================
        self._add_log("CEO", "Delegating to Underwriting Department")
        workflow.logger.info("CEO: Starting underwriting review...")

        # Prepare loan data with analysis for underwriting
        underwriting_input = {
            **self.loan_data,
            "analysis": analysis_result,
            "loan_number": self.loan_number
        }

        underwriting_result = await workflow.execute_child_workflow(
            UnderwritingWorkflow.run,
            args=[underwriting_input],
            id=f"{workflow.info().workflow_id}-underwriting",
            retry_policy=RetryPolicy(maximum_attempts=1)
        )

        self.automated_uw_decision = underwriting_result.get("decision", "REFER_TO_HUMAN")
        self.risk_evaluation = underwriting_result.get("risk_evaluation", {})

        workflow.logger.info(f"Underwriting completed with decision: {self.automated_uw_decision}")
        self._add_log("Underwriting", f"Decision: {self.automated_uw_decision}")

        # Persist underwriting results to SQL (including status update)
        await workflow.execute_activity(
            update_loan_metadata,
            args=[workflow.info().workflow_id, {
                "underwriting_decision": self.automated_uw_decision,
                "risk_evaluation": self.risk_evaluation,
                "status": "Underwriting Complete"
            }],
            start_to_close_timeout=timedelta(seconds=30)
        )

        # Check automated underwriting decision
        if self.automated_uw_decision == "REFER_TO_HUMAN":
            self._add_log("CEO", "Underwriting referred for additional human review")
            # For now, we'll still proceed to closing but mark for review
            # In production, might wait for another human gate here

        # =========================================
        # Phase 4: Closing
        # =========================================
        if self.automated_uw_decision == "CLEAR_TO_CLOSE":
            self.current_stage = LoanStage.CLOSING
            self._add_log("CEO", "CLEAR TO CLOSE - Moving to closing phase")
            workflow.logger.info("CEO: Loan is Clear to Close!")
        else:
            self.current_stage = LoanStage.CLOSING
            self._add_log("CEO", "Moving to closing with conditions")
            workflow.logger.info("CEO: Moving to closing with conditions")

        # Update SQL to reflect CLOSING stage
        await workflow.execute_activity(
            update_loan_metadata,
            args=[workflow.info().workflow_id, {
                "status": "Clear to Close" if self.automated_uw_decision == "CLEAR_TO_CLOSE" else "Closing with Conditions",
                "loan_stage": LoanStage.CLOSING.value
            }],
            start_to_close_timeout=timedelta(seconds=30)
        )

        # Generate Final Approval Letter
        workflow.logger.info("CEO: Generating Final Approval Letter...")
        self._add_log("DocGen MCP", "Generating Final Approval Letter...")

        applicant_info = self.loan_data.get("applicant_info", {})
        doc_data = {
            "workflow_id": workflow.info().workflow_id,
            "name": applicant_info.get("name", applicant_name),
            "email": applicant_info.get("email", ""),
            "property_value": self.loan_data.get("property_value", 0),
            "down_payment": self.loan_data.get("down_payment", 0),
            "loan_amount": self.loan_data.get("loan_amount", 0),
            "rate": 6.5,
            "term": 30
        }

        approval_doc = await workflow.execute_activity(
            generate_document,
            args=["Final Approval Letter", doc_data, {}],
            start_to_close_timeout=timedelta(seconds=60)
        )

        workflow.logger.info(f"Final Approval Letter generated: {approval_doc.get('public_url')}")
        self._add_log("DocGen MCP", f"Final Approval Letter generated: {approval_doc.get('public_url')}")

        # Send congratulations email
        applicant_email = applicant_info.get("email", "")
        if applicant_email:
            workflow.logger.info("CEO: Sending congratulations email...")
            self._add_log("Comms MCP", "Sending congratulations notification...")

            await workflow.execute_activity(
                send_email,
                args=["loan_funded", applicant_email, {
                    "name": applicant_info.get("name", applicant_name),
                    "loan_amount": self.loan_data.get("loan_amount", 0),
                    "approval_letter_url": approval_doc.get("public_url"),
                    "subject": "Congratulations! Your Loan is Funded"
                }],
                start_to_close_timeout=timedelta(seconds=30)
            )

            workflow.logger.info(f"Congratulations email sent to {applicant_email}")
            self._add_log("Comms MCP", f"Email sent to {applicant_email}: Congratulations! Your loan is funded")

        # =========================================
        # Final: Archive Completed Loan
        # =========================================
        self.current_stage = LoanStage.ARCHIVED
        self._add_log("CEO", "Loan lifecycle COMPLETED - Archiving")

        # Final status update - persist to SQL columns
        await workflow.execute_activity(
            update_loan_metadata,
            args=[workflow.info().workflow_id, {
                "status": "Funded",
                "loan_stage": LoanStage.ARCHIVED.value,
                "final_status": "COMPLETED",
                "underwriting_decision": self.automated_uw_decision
            }],
            start_to_close_timeout=timedelta(seconds=30)
        )

        workflow.logger.info(f"CEO Workflow completed for {applicant_name}")
        return "COMPLETED"
