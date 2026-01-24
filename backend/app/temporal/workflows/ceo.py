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
    from .managers import LeadCaptureWorkflow, ProcessingWorkflow


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

        workflow.logger.info(f"Lead Capture completed with AI recommendation: {ai_recommendation}")
        self._add_log("Lead Capture", f"Phase completed. AI Recommendation: {ai_recommendation}")
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
        # Future Phases (Placeholder)
        # =========================================
        # Phase 3: Underwriting
        # self.current_stage = LoanStage.UNDERWRITING
        # underwriting_result = await workflow.execute_child_workflow(...)

        # Phase 4: Closing
        # self.current_stage = LoanStage.CLOSING
        # closing_result = await workflow.execute_child_workflow(...)

        # =========================================
        # Final: Archive Completed Loan
        # =========================================
        self.current_stage = LoanStage.ARCHIVED
        self._add_log("CEO", "Loan lifecycle COMPLETED - Archiving")

        workflow.logger.info(f"CEO Workflow completed for {applicant_name}")
        return "COMPLETED"
