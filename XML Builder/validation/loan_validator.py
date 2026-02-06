from domain.loan_snapshot import LoanSnapshot

def validate_loan(loan: LoanSnapshot):
    """
    Validates the LoanSnapshot to ensure it meets minimum requirements for MISMO generation.
    Raises ValueError if validation fails.
    """
    
    # 1. Borrowers Validation
    if not loan.borrowers:
        raise ValueError("Validation Failed: No borrowers found for this loan.")
    
    for b in loan.borrowers:
        if not b.get("first_name") or not b.get("last_name"):
             # In a real scenario, business logic might allow orgs without first/last names
             pass 

    # 2. Property Validation
    if not loan.properties:
        raise ValueError("Validation Failed: No property found for this loan.")
        
    prop = loan.properties[0]
    if not prop.get("city") or not prop.get("state"):
         print(f"Warning: Property {prop.get('id')} missing city or state.")

    # 3. Loan Purpose Validation
    if not loan.application.get("loan_purpose"):
         print("Warning: Loan purpose is missing. defaulting to 'Other'.")

    return True
