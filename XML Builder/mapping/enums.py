from enum import Enum

class LoanPurpose(Enum):
    PURCHASE = "Purchase"
    REFINANCE = "Refinance"
    Other = "Other"

class PropertyState(Enum):
    CA = "CA"
    TX = "TX"
    NY = "NY"
    # Add other states as needed

class BorrowerType(Enum):
    INDIVIDUAL = "Individual"
    ORGANIZATION = "Organization"
