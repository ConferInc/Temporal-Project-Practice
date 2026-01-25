"""
Pyramid Architecture: Level 2 - The Department Managers (Child Workflows)

These child workflows are orchestrated by the CEO (LoanLifecycleWorkflow).
Each manager handles a specific phase of the loan lifecycle:

1. LeadCaptureWorkflow - Initial application intake
2. ProcessingWorkflow - Document verification and processing
3. UnderwritingWorkflow - Risk evaluation and final approval
"""
from datetime import timedelta
from typing import Any
from temporalio import workflow

# Import MCP Activities
with workflow.unsafe.imports_passed_through():
    from app.temporal.activities.mcp_comms import send_email
    from app.temporal.activities.mcp_encompass import create_loan_file
    from app.temporal.activities.mcp_docgen import generate_document
    # Legacy Activities for AI Analysis
    from app.temporal.activities.legacy import analyze_document, read_pdf_content
    # Underwriting Activities
    from app.temporal.activities.mcp_underwriting import verify_signature, evaluate_risk


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
            Dict with 'recommendation', 'loan_data', 'loan_number', 'analysis'
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

        # Step 3: AI Document Analysis - The "Brain"
        workflow.logger.info("Starting AI document analysis...")
        file_paths = applicant_data.get("file_paths", {})
        total_confidence = 0.0
        analysis_count = 0

        # Track AI extracted data for return
        ai_extracted_income = 0
        pay_stub_income = 0
        tax_income = 0
        extracted_name = None
        extracted_credit_score = 0

        # Analyze Pay Stub (for income verification)
        pay_stub_path = file_paths.get("pay_stub")
        if pay_stub_path:
            try:
                pay_stub_text = await workflow.execute_activity(
                    read_pdf_content,
                    args=[pay_stub_path],
                    start_to_close_timeout=timedelta(seconds=60)
                )
                pay_analysis = await workflow.execute_activity(
                    analyze_document,
                    args=[pay_stub_text, "financial_auditor"],
                    start_to_close_timeout=timedelta(seconds=60)
                )
                # Capture the extracted data
                pay_stub_income = pay_analysis.annual_income or 0
                if pay_analysis.applicant_name and pay_analysis.applicant_name != "Unknown":
                    extracted_name = pay_analysis.applicant_name

                # Confidence based on whether income was extracted
                if pay_analysis.annual_income > 0:
                    total_confidence += 0.9
                else:
                    total_confidence += 0.3
                analysis_count += 1
                workflow.logger.info(f"Pay stub analysis complete: income={pay_analysis.annual_income}")
            except Exception as e:
                workflow.logger.warning(f"Pay stub analysis failed: {e}")
                total_confidence += 0.5
                analysis_count += 1

        # Analyze Tax Return (for income verification)
        tax_path = file_paths.get("tax_document")
        if tax_path:
            try:
                tax_text = await workflow.execute_activity(
                    read_pdf_content,
                    args=[tax_path],
                    start_to_close_timeout=timedelta(seconds=60)
                )
                tax_analysis = await workflow.execute_activity(
                    analyze_document,
                    args=[tax_text, "financial_auditor"],
                    start_to_close_timeout=timedelta(seconds=60)
                )
                # Capture the extracted data
                tax_income = tax_analysis.annual_income or 0
                if tax_analysis.applicant_name and tax_analysis.applicant_name != "Unknown":
                    extracted_name = tax_analysis.applicant_name

                # Confidence based on whether income was extracted
                if tax_analysis.annual_income > 0:
                    total_confidence += 0.9
                else:
                    total_confidence += 0.3
                analysis_count += 1
                workflow.logger.info(f"Tax return analysis complete: income={tax_analysis.annual_income}")
            except Exception as e:
                workflow.logger.warning(f"Tax return analysis failed: {e}")
                total_confidence += 0.5
                analysis_count += 1

        # Use the highest extracted income (more reliable)
        ai_extracted_income = max(pay_stub_income, tax_income)

        # Check for income mismatch
        stated_income_raw = applicant_data.get("applicant_info", {}).get("stated_income", "0")
        try:
            # Handle income as string (from form) or number
            stated_income = int(str(stated_income_raw).replace(",", "").replace("$", ""))
        except (ValueError, TypeError):
            stated_income = 0

        # Calculate mismatch - flag if difference > 20%
        income_mismatch = False
        if ai_extracted_income > 0 and stated_income > 0:
            diff_pct = abs(ai_extracted_income - stated_income) / stated_income
            income_mismatch = diff_pct > 0.20
            workflow.logger.info(f"Income comparison: stated={stated_income}, verified={ai_extracted_income}, mismatch={income_mismatch}")

        # Calculate average confidence and set recommendation
        avg_confidence = total_confidence / max(analysis_count, 1)
        workflow.logger.info(f"AI analysis complete. Average confidence: {avg_confidence:.2f}")

        if income_mismatch:
            self.ai_recommendation = "MANUAL_REVIEW"
            workflow.logger.info("AI recommends: MANUAL_REVIEW (income mismatch detected)")
        elif avg_confidence > 0.8:
            self.ai_recommendation = "APPROVED"
            workflow.logger.info("AI recommends: APPROVED (high confidence)")
        else:
            self.ai_recommendation = "MANUAL_REVIEW"
            workflow.logger.info("AI recommends: MANUAL_REVIEW (needs human attention)")

        workflow.logger.info("Lead Capture complete - returning to CEO for human approval gate")

        # Build analysis result object
        analysis_result = {
            "verified_income": ai_extracted_income,
            "pay_stub_income": pay_stub_income,
            "tax_income": tax_income,
            "stated_income": stated_income,
            "income_mismatch": income_mismatch,
            "confidence": round(avg_confidence, 2),
            "extracted_name": extracted_name,
            "credit_score": extracted_credit_score,
        }

        # Return immediately - NO GATE HERE
        # The CEO workflow handles the human approval gate
        return {
            "recommendation": self.ai_recommendation,
            "loan_data": self.loan_data,
            "loan_number": self.loan_number,
            "analysis": analysis_result
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
        self.logs.append({
            "agent": agent,
            "message": message,
            "timestamp": workflow.now().isoformat()
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


@workflow.defn
class UnderwritingWorkflow:
    """
    Level 2 Manager: Underwriting Department

    Responsibilities:
    1. Verify borrower signature on disclosures
    2. Evaluate loan risk (DTI, credit score, loan limits)
    3. Make final underwriting decision

    Returns: Dict with 'decision' (CLEAR_TO_CLOSE or REFER_TO_HUMAN) and details
    """

    def __init__(self) -> None:
        self.status = "Not Started"
        self.decision = None
        self.risk_evaluation = {}
        self.logs = []

    @workflow.query
    def get_status(self) -> str:
        """Query the current underwriting status"""
        return self.status

    @workflow.query
    def get_decision(self) -> str:
        """Query the underwriting decision"""
        return self.decision

    @workflow.query
    def get_risk_evaluation(self) -> dict:
        """Query the risk evaluation details"""
        return self.risk_evaluation

    @workflow.query
    def get_logs(self) -> list:
        """Query the underwriting logs for audit trail"""
        return self.logs

    def _log(self, agent: str, message: str):
        """Add entry to audit trail"""
        self.logs.append({
            "agent": agent,
            "message": message,
            "timestamp": workflow.now().isoformat()
        })

    @workflow.run
    async def run(self, loan_data: dict) -> dict:
        """
        Execute the Underwriting phase.

        Args:
            loan_data: Dict containing loan information including analysis results

        Returns:
            Dict with 'decision', 'risk_evaluation', 'status'
        """
        workflow.logger.info("UnderwritingWorkflow started")
        self.status = "Underwriting"
        self._log("Underwriting Manager", "Underwriting phase started")

        # Extract workflow ID
        workflow_id = workflow.info().workflow_id.replace("-underwriting", "")

        # Step 1: Verify Signature
        workflow.logger.info("Verifying borrower signature...")
        self.status = "Verifying Signature"
        self._log("Underwriting Manager", "Verifying borrower signature on disclosures...")

        signature_result = await workflow.execute_activity(
            verify_signature,
            args=[workflow_id],
            start_to_close_timeout=timedelta(seconds=30)
        )

        if not signature_result.get("verified"):
            self.decision = "SIGNATURE_MISSING"
            self._log("Underwriting Manager", "ERROR: Signature not found on disclosures")
            workflow.logger.warning("Signature verification failed - document not signed")
            return {
                "decision": "SIGNATURE_MISSING",
                "status": "Failed",
                "error": "Borrower signature not found"
            }

        self._log("Underwriting Manager", f"Signature verified at {signature_result.get('verified_at')}")
        workflow.logger.info("Signature verified successfully")

        # Step 2: Evaluate Risk
        workflow.logger.info("Evaluating loan risk...")
        self.status = "Evaluating Risk"
        self._log("Risk Analyst", "Evaluating loan against underwriting criteria...")

        risk_result = await workflow.execute_activity(
            evaluate_risk,
            args=[loan_data],
            start_to_close_timeout=timedelta(seconds=30)
        )

        self.risk_evaluation = risk_result
        self.decision = risk_result.get("decision", "REFER_TO_HUMAN")

        # Log risk evaluation results
        self._log("Risk Analyst", f"Credit Score: {risk_result.get('credit_score', 'N/A')}")
        self._log("Risk Analyst", f"DTI Ratio: {risk_result.get('dti_ratio', 'N/A')}%")
        self._log("Risk Analyst", f"Loan Amount: ${risk_result.get('loan_amount', 0):,.2f}")

        if risk_result.get("issues"):
            for issue in risk_result["issues"]:
                self._log("Risk Analyst", f"Issue: {issue}")

        self._log("Underwriting Manager", f"Decision: {self.decision}")
        workflow.logger.info(f"Underwriting decision: {self.decision}")

        # Step 3: Final status update
        if self.decision == "CLEAR_TO_CLOSE":
            self.status = "Clear to Close"
            self._log("Underwriting Manager", "Loan approved - Clear to Close!")
        else:
            self.status = "Referred for Review"
            self._log("Underwriting Manager", "Loan referred for additional human review")

        workflow.logger.info("Underwriting phase completed")

        return {
            "decision": self.decision,
            "risk_evaluation": self.risk_evaluation,
            "status": self.status
        }
