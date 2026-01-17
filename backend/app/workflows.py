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

            # Analyze Credit Report
            credit_text = await workflow.execute_activity(
                read_pdf_content,
                input_data['file_paths']['credit_document'],
                start_to_close_timeout=timedelta(seconds=10)
            )
            credit_analysis = await workflow.execute_activity(
                analyze_document,
                credit_text,
                start_to_close_timeout=timedelta(minutes=1)
            )
            
            # Analyze ID
            id_text = await workflow.execute_activity(
                read_pdf_content,
                input_data['file_paths']['id_document'],
                start_to_close_timeout=timedelta(seconds=10)
            )

            # Store AI Results
            self.data['ai_analysis'] = {
                "tax_extracted": tax_analysis,
                "credit_extracted": credit_analysis
            }
            
        except Exception as e:
            self.status = f"Analysis Failed: {str(e)}"
            raise e

        # 2. Verification Logic
        stated_income = float(input_data['applicant_info']['stated_income'])
        verified_income = float(tax_analysis.annual_income)
        # Use Credit Score from Credit Report, invalidating potential bad data from Tax Return
        credit_score = credit_analysis.credit_score 

        self.data['verification'] = {
            "stated_income": stated_income,
            "verified_income": verified_income,
            "income_match": abs(stated_income - verified_income) < 5000, # $5k Tolerance
            "credit_score": credit_score
        }

        # 3. Decision Engine
        if credit_score < 620:
            self.status = "Auto-Rejected (Low Credit)"
            # await workflow.execute_activity(send_email, "Rejected...", ...)
            return "Rejected"
        
        if not self.data['verification']['income_match']:
            self.status = "Flagged: Income Mismatch"
            # Proceed to manual review...

        if credit_score > 740 and verified_income > 60000 and self.data['verification']['income_match']:
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