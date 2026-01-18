import asyncio 
from datetime import timedelta
from temporalio import workflow
from temporalio.exceptions import ApplicationError

# Import activities
from app.activities import analyze_document, read_pdf_content, send_email_mock, organize_files, LoanData

@workflow.defn
class LoanProcessWorkflow:
    def __init__(self) -> None:
        self.is_approved = None 
        self.status = "Started"
        self.data = None # Store full object

    @workflow.signal
    @workflow.signal
    def human_approval_signal(self, approved: bool):
        self.is_approved = approved
        self.status = "Human Reviewed" if approved else "Rejected by Manager"
        self.is_waiting = False

    @workflow.query
    def get_status(self) -> str:
        return self.status

    @workflow.query
    def get_loan_data(self) -> dict:
        return self.data

    @workflow.run
    async def run(self, input_data: dict) -> str:
        workflow.logger.info(f"Workflow started for {input_data['applicant_info']['name']}")
        
        # --- Step 1: The File Clerk (Organize Workspace) ---
        self.status = "File Clerk: Organizing Documents..."
        
        # Call the File Clerk Agent
        cleaned_file_paths = await workflow.execute_activity(
            "organize_files",
            args=[input_data['applicant_info']['name'], input_data['file_paths']],
            start_to_close_timeout=timedelta(seconds=10)
        )
        
        # Update our data execution context with clean paths
        self.data = input_data
        self.data['file_paths'] = cleaned_file_paths
        
        # --- Step 2: The Analyst Agents (Parallel Execution) ---
        self.status = "Agents: Analyzing Documents in Parallel..."
        
        # Define the content-reading tasks first (Sequential for now until read_pdf is lighter, or parallel if IO bound)
        # Actually, let's just do them inside the gather if possible, but workflow logic suggests:
        # We need text to pass to analyze. 
        # Pattern: We can create async functions (sub-flows) or just chain them.
        # Let's use simple chaining for clarity in the gather.
        
        async def job_auditor():
            """Reads Tax Return and acts as Financial Auditor"""
            text = await workflow.execute_activity(
                read_pdf_content, args=[cleaned_file_paths['tax_document']], 
                start_to_close_timeout=timedelta(seconds=20)
            )
            return await workflow.execute_activity(
                analyze_document, args=[text, "financial_auditor"],
                start_to_close_timeout=timedelta(minutes=1)
            )

        async def job_verifier():
            """Reads Credit Report & ID and acts as Identity Verifier"""
            # We can process both sequentially within this 'Verifier' job
            credit_text = await workflow.execute_activity(
                read_pdf_content, args=[cleaned_file_paths['credit_document']],
                start_to_close_timeout=timedelta(seconds=20)
            )
            return await workflow.execute_activity(
                analyze_document, args=[credit_text, "identity_verifier"],
                start_to_close_timeout=timedelta(minutes=1)
            )
            
        # Launch Agents in Parallel!
        # This is the "Magic" of Temporal/Asyncio
        results = await asyncio.gather(job_auditor(), job_verifier())
        
        audit_result, verify_result = results[0], results[1]
        
        self.data['ai_analysis'] = {
            "financial_audit": audit_result,
            "identity_verification": verify_result
        }
        
        # --- Step 3: Synthesis & Verification ---
        stated_income = float(input_data['applicant_info']['stated_income'])
        verified_income = float(audit_result.annual_income)
        credit_score = verify_result.credit_score
        
        income_match = abs(stated_income - verified_income) < 5000
        
        self.data['verification'] = {
            "stated_income": stated_income,
            "verified_income": verified_income,
            "income_match": income_match,
            "credit_score": credit_score
        }
        
        workflow.logger.info(f"Verification Complete: Score={credit_score}, Match={income_match}")

        # --- Step 4: The Boss Decides (Logic Gates) ---
        if credit_score < 620:
            self.status = "Auto-Rejected (Low Credit)"
            return "Rejected"
        
        if not income_match:
            self.status = "Flagged: Income Mismatch"
            # Proceeds to manual review below...
        
        elif credit_score > 740 and verified_income > 60000:
             self.status = "Auto-Approved"
             return "Approved"
        
        # Default: Manual Review
        self.status = "Pending Manual Review"
        self.is_waiting = True
        
        await workflow.wait_condition(lambda: not self.is_waiting)
        
        if self.is_approved:
            self.status = "Approved"
            return "Approved"
        else:
            self.status = "Rejected"
            return "Rejected"