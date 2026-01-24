import asyncio 
from datetime import timedelta
from temporalio import workflow
from temporalio.exceptions import ApplicationError

# Use absolute import for sibling package
from app.temporal.activities import analyze_document, read_pdf_content, send_email_mock, organize_files
# LoanData was likely defined in the old activities file, so we import it from there too
from app.temporal.activities.legacy import LoanData
@workflow.defn
class LoanProcessWorkflow:
    def __init__(self) -> None:
        self.is_approved = None 
        self.status = "Started"
        self.data = None 
        self.logs = [] # 🔹 NEW: Central Log Store

    @workflow.signal
    def human_approval_signal(self, approved: bool):
        self.is_approved = approved
        self.status = "Human Reviewed" if approved else "Rejected by Manager"
        self.is_waiting = False
        self._add_log("Agent 5 (Human Manager)", "signal", "Final Decision submitted via Dashboard.")

    @workflow.query
    def get_status(self) -> str:
        return self.status

    @workflow.query
    def get_loan_data(self) -> dict:
        return self.data
    
    @workflow.query
    def get_logs(self) -> list:
        """Return the worker-produced logs"""
        return self.logs

    def _add_log(self, agent: str, type: str, message: str):
        # Simple formatted log entry using deterministic time
        entry = {
            "agent": agent,
            "original_type": type,
            "message": message,
            "timestamp": workflow.now().isoformat()
        }
        self.logs.append(entry)

    @workflow.run
    async def run(self, input_data: dict) -> str:
        workflow.logger.info(f"Workflow started for {input_data['applicant_info']['name']}")
        self._add_log("System", "start", "Application received and workflow started.")
        
        # --- Step 1: File Clerk ---
        self.status = "File Clerk: Organizing Documents..."
        
        cleaned_file_paths = await workflow.execute_activity(
            organize_files,
            args=[input_data['applicant_info']['name'], input_data['file_paths']],
            start_to_close_timeout=timedelta(seconds=10)
        )
        self._add_log("Agent 0 (File Clerk)", "init_loan_folder", "Created secure folder structure for applicant documents.")
        
        self.data = input_data
        self.data['file_paths'] = cleaned_file_paths
        
        # --- Step 2: Analysts ---
        self.status = "Agents: Analyzing Documents in Parallel..."
        
        async def job_auditor():
            if 'tax_document' not in cleaned_file_paths:
                return LoanData(applicant_name="Unknown", missing_docs=["Tax Return"])

            text = await workflow.execute_activity(
                read_pdf_content, args=[cleaned_file_paths['tax_document']], 
                start_to_close_timeout=timedelta(seconds=20)
            )
            self._add_log("Agent 1 (OCR)", "read_pdf_content", "Extracted text content from Tax Return.")
            
            result = await workflow.execute_activity(
                analyze_document, args=[text, "financial_auditor"],
                start_to_close_timeout=timedelta(minutes=1)
            )
            self._add_log("Agent 2 (Analyst)", "analyze_document", "Performed Financial Audit on Tax Return.")
            return result

        async def job_verifier():
            if 'credit_document' not in cleaned_file_paths:
                 return LoanData(applicant_name="Unknown", missing_docs=["Credit Report"])

            credit_text = await workflow.execute_activity(
                read_pdf_content, args=[cleaned_file_paths['credit_document']],
                start_to_close_timeout=timedelta(seconds=20)
            )
            self._add_log("Agent 1 (OCR)", "read_pdf_content", "Extracted text content from Credit Report.")

            result = await workflow.execute_activity(
                analyze_document, args=[credit_text, "identity_verifier"],
                start_to_close_timeout=timedelta(minutes=1)
            )
            self._add_log("Agent 3 (Risk)", "check_credit_score", "Checked internal credit guidelines.")
            return result
            
        results = await asyncio.gather(job_auditor(), job_verifier())
        audit_result, verify_result = results[0], results[1]
        
        self.data['ai_analysis'] = {
            "financial_audit": audit_result,
            "identity_verification": verify_result
        }
        
        # --- Step 3: Synthesis ---
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
        
        # --- Step 4: Logic Gates ---
        if credit_score < 620:
            self.status = "Auto-Rejected (Low Credit)"
            self._add_log("System", "decision", f"Auto-Rejected due to low credit score ({credit_score}).")
            return "Rejected"
        
        if not income_match:
            self.status = "Flagged: Income Mismatch"
            self._add_log("System", "flag", f"Flagged for Income Mismatch (Stated: {stated_income}, Verified: {verified_income}).")
        
        elif credit_score > 740 and verified_income > 60000:
             self.status = "Auto-Approved"
             self._add_log("System", "decision", "Auto-Approved based on high credit and income.")
             return "Approved"
        
        # Manual Review
        self.status = "Pending Manual Review"
        self.is_waiting = True
        self._add_log("System", "wait", "Application queued for Manager Review.")
        
        await workflow.wait_condition(lambda: not self.is_waiting)
        
        if self.is_approved:
            return "Approved"
        else:
            return "Rejected"