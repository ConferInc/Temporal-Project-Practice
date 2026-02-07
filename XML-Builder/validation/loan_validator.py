"""
Loan Validator
Validates LoanSnapshot before XML generation
"""
from domain.loan_snapshot import LoanSnapshot


def validate_loan_snapshot(snapshot: LoanSnapshot) -> None:
    """
    Validates that the loan snapshot has all required data for MISMO generation
    Raises ValueError if validation fails
    """
    
    # Check application exists
    if not snapshot.application:
        raise ValueError("Application data is missing")
    
    # Check for at least one customer
    if not snapshot.customers:
        raise ValueError("At least one customer is required")
    
    # Check for at least one borrower (not just any customer)
    borrower_roles = ["BORROWER", "CO_BORROWER", "COBORROWER"]
    has_borrower = any(
        c.get("role", "").upper() in borrower_roles
        for c in snapshot.customers
    )
    if not has_borrower:
        raise ValueError("At least one customer must have role 'Borrower' or 'CoBorrower'")
    
    # Check property exists
    if not snapshot.property:
        raise ValueError("Property data is missing")
    
    # Check loan purpose exists
    if not snapshot.application.get("loan_purpose"):
        raise ValueError("Loan purpose is required")
    
    # Check loan amount exists
    if not snapshot.application.get("loan_amount"):
        raise ValueError("Loan amount is required")
    
    print("✓ Loan validation passed")
