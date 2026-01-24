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
    from app.temporal.activities.mcp_docgen import generate_document


@workflow.defn
class LeadCaptureWorkflow:
    """
    Level 2 Manager: Lead Capture Department

    Responsibilities:
    1. Create loan file in Encompass LOS
    2. Send welcome email to applicant
    3. Return immediately with recommendation (NO GATE - gate is in CEO)

    Returns: Dict with 'recommendation', 'loan_data', 'loan_number'
    """

    def __init__(self) -> None:
        self.ai_recommendation = "PENDING"  # AI's suggestion
        self.loan_number = None
        self.loan_data = {}  # Loan data for real-time editing

    @workflow.query
    def get_loan_number(self) -> str:
        """Query the Encompass loan number"""
        return self.loan_number

    @workflow.query
    def get_loan_data(self) -> dict:
        """Query the current loan data"""
        return self.loan_data

    @workflow.query
    def get_ai_recommendation(self) -> str:
        """Query the AI's recommendation"""
        return self.ai_recommendation

    @workflow.run
    async def run(self, applicant_data: dict) -> dict:
        """
        Execute the Lead Capture phase.

        Args:
            applicant_data: Dict containing applicant_info and file_paths

        Returns:
            Dict with 'recommendation', 'loan_data', 'loan_number'
            NOTE: No gate here - CEO handles the human approval gate
        """
        # Initialize loan_data with input args
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

        # Step 3: Set AI recommendation (in production, this would be actual AI analysis)
        self.ai_recommendation = "PENDING_REVIEW"
        workflow.logger.info("Lead Capture complete - returning to CEO for human approval gate")

        # Return immediately - NO GATE HERE
        # The CEO workflow handles the human approval gate
        return {
            "recommendation": self.ai_recommendation,
            "loan_data": self.loan_data,
            "loan_number": self.loan_number
        }


@workflow.defn
class ProcessingWorkflow:
    """
    Level 2 Manager: Processing Department

    Responsibilities:
    1. Generate Initial Disclosures
    2. Verify documents
    3. Run credit checks
    4. Prepare for underwriting

    Returns: "COMPLETED"
    """

    def __init__(self) -> None:
        self.status = "Not Started"
        self.generated_docs = []
        self.logs = []

    @workflow.query
    def get_status(self) -> str:
        """Query the current processing status"""
        return self.status

    @workflow.query
    def get_generated_docs(self) -> list:
        """Query the list of generated documents"""
        return self.generated_docs

    @workflow.query
    def get_logs(self) -> list:
        """Query the processing logs for audit trail"""
        return self.logs

    def _log(self, agent: str, message: str):
        """Add entry to audit trail"""
        from datetime import datetime
        self.logs.append({
            "agent": agent,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })

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
        self._log("Processing Manager", "Processing phase started")

        # Step 1: Extract loan data for document generation
        applicant_info = loan_data.get("applicant_info", {})
        workflow_id = workflow.info().workflow_id.replace("-processing", "")

        # Get financial data (from funnel or defaults)
        loan_amount = loan_data.get("loan_amount", 0)
        property_value = loan_data.get("property_value", 0)
        down_payment = loan_data.get("down_payment", 0)

        # If loan_amount not provided, calculate from property value - down payment
        if not loan_amount and property_value:
            loan_amount = property_value - down_payment

        # Step 2: Generate Initial Disclosures document
        workflow.logger.info("Generating Initial Disclosures...")
        self.status = "Generating Documents"
        self._log("DocGen MCP", "Generating Initial Disclosures...")

        doc_data = {
            "workflow_id": workflow_id,
            "name": applicant_info.get("name", "Unknown Borrower"),
            "email": applicant_info.get("email", ""),
            "property_value": property_value,
            "down_payment": down_payment,
            "loan_amount": loan_amount,
            "rate": 6.5,
            "term": 30
        }

        doc_result = await workflow.execute_activity(
            generate_document,
            args=["Initial Disclosures", doc_data, {}],
            start_to_close_timeout=timedelta(seconds=60)
        )

        self.generated_docs.append(doc_result)
        workflow.logger.info(f"Initial Disclosures generated: {doc_result.get('public_url')}")
        self._log("DocGen MCP", f"Initial Disclosures generated: {doc_result.get('public_url')}")

        # Step 3: Document verification placeholder
        workflow.logger.info("Verifying documents...")
        self.status = "Verifying Documents"
        self._log("Processing Manager", "Document verification in progress...")

        # In production, this would:
        # - Execute document verification activities
        # - Run credit check activities
        # - Validate income against tax returns

        self.status = "Documents Verified"
        self._log("Processing Manager", "All documents verified successfully")
        workflow.logger.info("Processing phase completed")

        return "COMPLETED"
