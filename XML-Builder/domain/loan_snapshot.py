"""
Loan Snapshot Domain Model
Aggregates all loan-related data into a single structured object
"""
from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass
class LoanSnapshot:
    """
    Complete snapshot of a loan application with all related entities
    """
    application: Dict[str, Any]
    customers: List[Dict[str, Any]]  # Changed from borrowers
    property: Dict[str, Any]
    assets: List[Dict[str, Any]]
    liabilities: List[Dict[str, Any]]
    
    def __post_init__(self):
        """Basic validation"""
        if not self.application:
            raise ValueError("Application data is required")
        
        if not self.customers:
            raise ValueError("At least one customer is required")
        
        # Validate at least one borrower exists
        has_borrower = any(
            c.get("role", "").upper() in ["BORROWER", "CO_BORROWER", "COBORROWER"]
            for c in self.customers
        )
        if not has_borrower:
            raise ValueError("At least one customer must have role 'Borrower' or 'CoBorrower'")
