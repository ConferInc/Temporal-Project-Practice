"""
Application Mapper
Maps application table data to MISMO loan-level fields
"""
from . import enums


def map_loan_purpose(db_value: str) -> str:
    """Map database loan_purpose to MISMO LoanPurposeType"""
    if not db_value:
        return ""
    return enums.LOAN_PURPOSE.get(db_value.upper(), db_value)


def map_occupancy_type(db_value: str) -> str:
    """Map database occupancy_type to MISMO OccupancyType"""
    if not db_value:
        return ""
    return enums.OCCUPANCY_TYPE.get(db_value.upper(), db_value)


def map_application_status(db_value: str) -> str:
    """Map application status (if needed for MISMO)"""
    # Most MISMO files don't include workflow status
    # but this can be extended if needed
    return db_value or ""


def extract_loan_amount(application: dict) -> str:
    """Extract and format loan amount"""
    amount = application.get("loan_amount")
    if amount is None:
        return "0"
    return str(amount)


def extract_application_number(application: dict) -> str:
    """Extract application/loan number"""
    return application.get("application_number") or ""
