from typing import Optional
from mapping.enums import LoanPurpose

def map_loan_purpose(db_value: str) -> str:
    """Maps database loan purpose to MISMO LoanPurposeType."""
    if not db_value:
        return "Other"
    
    mapping = {
        "PURCHASE": LoanPurpose.PURCHASE.value,
        "REFINANCE": LoanPurpose.REFINANCE.value,
        "CASH_OUT_REFINANCE": LoanPurpose.REFINANCE.value 
    }
    return mapping.get(db_value.upper(), "Other")

def map_state_code(db_value: str) -> str:
    """Maps state code, ensuring it's 2 chars uppercase."""
    if not db_value:
        return ""
    return db_value.upper()[:2]

def map_borrower_type(db_value: str) -> str:
    """Maps borrower type."""
    if db_value and db_value.lower() == "company":
        return "Organization"
    return "Individual"
