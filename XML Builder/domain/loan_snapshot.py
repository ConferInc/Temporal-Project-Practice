from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class LoanSnapshot:
    """
    aggregated view of a loan application.
    This object is the source of truth for XML generation.
    """
    application: Dict[str, Any]
    borrowers: List[Dict[str, Any]]
    properties: List[Dict[str, Any]]
    liabilities: List[Dict[str, Any]]

    def validate(self):
        """
        Basic validation to ensure critical components exist.
        Detailed validation should be in the validation module.
        """
        if not self.application:
            raise ValueError("LoanSnapshot is missing application data.")
        if not self.borrowers:
            raise ValueError("LoanSnapshot must have at least one borrower.")
