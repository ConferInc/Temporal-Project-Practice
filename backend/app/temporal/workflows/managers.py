"""
Pyramid Architecture: Level 2 - The Department Managers (Child Workflows)

These child workflows are orchestrated by the CEO (LoanLifecycleWorkflow).
Each manager handles a specific phase of the loan lifecycle:

1. LeadCaptureWorkflow - Initial application intake
2. ProcessingWorkflow - Document verification and processing
"""
from datetime import timedelta
from typing import Any
from temporalio import workflow

# Import MCP Activities
with workflow.unsafe.imports_passed_through():
    from app.temporal.activities.mcp_comms import send_email
    from app.temporal.activities.mcp_encompass import create_loan_file


@workflow.defn
class LeadCaptureWorkflow:
    """
    Level 2 Manager: Lead Capture Department

    Responsibilities:
    1. Create loan file in Encompass LOS
    2. Send welcome email to applicant
    3. Wait for human approval signal
    4. Allow real-time field updates via signals

    Returns: "APPROVED" or "REJECTED"
    """

    def __init__(self) -> None:
        self.human_decision = None
        self.loan_number = None
        self.loan_data = {}  # Mutable state for Encompass-style editing

    @workflow.signal
    def human_approval(self, approved: bool):
        """Signal handler for human manager approval"""
        self.human_decision = "APPROVED" if approved else "REJECTED"
        workflow.logger.info(f"LeadCapture received human decision: {self.human_decision}")

    @workflow.signal
    def update_field(self, field_name: str, value: Any):
        """Signal handler for real-time field updates from manager dashboard"""
        self.loan_data[field_name] = value
        workflow.logger.info(f"Manager updated {field_name} to {value}")

    @workflow.query
    def get_loan_number(self) -> str:
        """Query the Encompass loan number"""
        return self.loan_number

    @workflow.query
    def get_loan_data(self) -> dict:
        """Query the current (potentially modified) loan data"""
        return self.loan_data

    @workflow.run
    async def run(self, applicant_data: dict) -> str:
        """
        Execute the Lead Capture phase.

        Args:
            applicant_data: Dict containing applicant_info and file_paths

        Returns:
            "APPROVED" or "REJECTED"
        """
        # Initialize loan_data with input args for real-time editing
        self.loan_data = applicant_data.copy()
        workflow.logger.info(f"LeadCaptureWorkflow started for {applicant_data.get('applicant_info', {}).get('name', 'Unknown')}")

        # Step 1: Create loan file in Encompass
        loan_file_result = await workflow.execute_activity(
            create_loan_file,
            args=[{
                "applicant_name": applicant_data.get("applicant_info", {}).get("name", "Unknown"),
                "email": applicant_data.get("applicant_info", {}).get("email", ""),
                "stated_income": applicant_data.get("applicant_info", {}).get("stated_income", 0),
            }],
            start_to_close_timeout=timedelta(seconds=30)
        )
        self.loan_number = loan_file_result.get("loan_number")
        workflow.logger.info(f"Loan file created: {self.loan_number}")

        # Step 2: Send welcome email
        applicant_email = applicant_data.get("applicant_info", {}).get("email", "")
        if applicant_email:
            await workflow.execute_activity(
                send_email,
                args=["welcome", applicant_email, {"loan_number": self.loan_number}],
                start_to_close_timeout=timedelta(seconds=30)
            )
            workflow.logger.info(f"Welcome email sent to {applicant_email}")

        # Step 3: Wait for human approval signal
        workflow.logger.info("Waiting for human approval...")
        await workflow.wait_condition(lambda: self.human_decision is not None)

        workflow.logger.info(f"LeadCaptureWorkflow completed with: {self.human_decision}")
        return self.human_decision


@workflow.defn
class ProcessingWorkflow:
    """
    Level 2 Manager: Processing Department

    Responsibilities:
    1. Verify documents
    2. Run credit checks
    3. Prepare for underwriting

    Returns: "COMPLETED"
    """

    def __init__(self) -> None:
        self.status = "Not Started"

    @workflow.query
    def get_status(self) -> str:
        """Query the current processing status"""
        return self.status

    @workflow.run
    async def run(self, loan_data: dict) -> str:
        """
        Execute the Processing phase.

        Args:
            loan_data: Dict containing loan information

        Returns:
            "COMPLETED"
        """
        workflow.logger.info("ProcessingWorkflow started")
        self.status = "Processing"

        # Placeholder: In production, this would:
        # - Execute document verification activities
        # - Run credit check activities
        # - Validate income against tax returns
        workflow.logger.info("Started Processing Phase - Document verification in progress...")

        # Simulate processing time (in real implementation, this would be actual activities)
        self.status = "Documents Verified"
        workflow.logger.info("Processing phase completed")

        return "COMPLETED"
