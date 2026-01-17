from datetime import timedelta
from temporalio import workflow
from temporalio.exceptions import ApplicationError

# Import activities
from app.activities import analyze_document, read_pdf_content, send_email_mock, LoanData

@workflow.defn
class LoanProcessWorkflow:
    def __init__(self) -> None:
        self.is_approved = None 
        self.status = "Started"
        self.data = None # Store full object

    @workflow.signal
    def human_approval_signal(self, approved: bool):
        self.is_approved = approved
        self.status = "Human Reviewed" if approved else "Rejected by Manager"

    @workflow.query
    def get_status(self) -> str:
        return self.status

    @workflow.query
    def get_loan_data(self) -> dict:
        return self.data

    @workflow.run
    async def run(self, input_data: dict) -> str:
        # Input Data Structure:
        # {
        #   "applicant_info": { name, ssn, stated_income ... },
        #   "file_paths": { id_document, tax_document, pay_stub },
        #   "public_urls": { ... }
        # }
        
        self.data = input_data
        self.status = "Analyzing Documents"
        workflow.logger.info(f"Workflow started for {input_data['applicant_info']['name']}")

        # 1. Read & Analyze all files
        # Ideally we run these in parallel
        # For MVP, sequential is safer to debug
        
        try:
            # Analyze Tax Return
            tax_text = await workflow.execute_activity(
                read_pdf_content,
                input_data['file_paths']['tax_document'],
                start_to_close_timeout=timedelta(minutes=1)
            )
            tax_analysis = await workflow.execute_activity(
                analyze_document,
                tax_text,
                start_to_close_timeout=timedelta(minutes=2)
            )
            
            # Analyze ID
            id_text = await workflow.execute_activity(
                read_pdf_content,
                input_data['file_paths']['id_document'],
                start_to_close_timeout=timedelta(minutes=1)
            )
            # We reuse analyze_document, but in real world might have specific prompts
            # For now, it extracts generalized "Applicant Name", "Income", "Score"
            # Since ID doesn't have income, it might return 0 or None.
            
            # Update our data object with AI results
            self.data['ai_analysis'] = {
                "tax_extracted": tax_analysis,
                # "id_extracted": ... (Skip for MVP simplicity, assume Tax is truth source for income)
            }
            
        except Exception as e:
            self.status = f"Analysis Failed: {str(e)}"
            raise e

        # 2. Logic Verification
        self.status = "Verifying Data"
        
        stated_income = float(input_data['applicant_info']['stated_income'])
        verified_income = float(tax_analysis.annual_income)
        credit_score = tax_analysis.credit_score 
        
        # Store verification results for Dashboard
        self.data['verification'] = {
            "stated_income": stated_income,
            "verified_income": verified_income,
            "income_match": abs(stated_income - verified_income) < 5000, # 5k tolerance
            "credit_score": credit_score
        }

        # 3. Decision Logic
        if credit_score < 620:
             self.status = "Auto-Rejected (Low Credit)"
             # Send Email...
             return "Rejected"
             
        if not self.data['verification']['income_match']:
             # Major discrepancy
             self.status = "Flagged: Income Mismatch"
             # Must Wait for Manager
        else:
             if credit_score > 740 and verified_income > 60000:
                  self.status = "Auto-Approved"
                  self.is_approved = True
                  # Send Email
                  return "Approved"
             else:
                  self.status = "Underwriting Review"

        # 4. Human Loop
        await workflow.wait_condition(lambda: self.is_approved is not None)
        
        if self.is_approved:
            self.status = "Approved"
            return "Approved"
        else:
            self.status = "Rejected"
            return "Rejected"