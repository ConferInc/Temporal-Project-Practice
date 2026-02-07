"""
Liability Mapper
Maps liabilities table data to MISMO LIABILITY fields
"""
from . import enums
from typing import Dict


def map_liability_type(db_value: str) -> str:
    """Map liability_type to MISMO LiabilityType"""
    if not db_value:
        return "Other"
    return enums.LIABILITY_TYPE.get(db_value.upper(), db_value)


def format_liability_amount(amount) -> str:
    """Format liability amount for MISMO"""
    if amount is None:
        return "0"
    try:
        return str(float(amount))
    except (ValueError, TypeError):
        return "0"


def extract_liability_details(liability: Dict) -> Dict:
    """Extract all liability details for MISMO"""
    return {
        "liability_type": map_liability_type(liability.get("liability_type")),
        "creditor_name": liability.get("creditor_name") or "",
        "account_number": liability.get("account_number") or "",
        "unpaid_balance": format_liability_amount(liability.get("unpaid_balance")),
        "monthly_payment": format_liability_amount(liability.get("monthly_payment")),
        "months_remaining": liability.get("months_remaining") or 0,
        "to_be_paid_off": liability.get("to_be_paid_off_at_closing", False),
        "will_be_subordinated": liability.get("will_be_subordinated", False),
        "exclude_from_dti": liability.get("exclude_from_dti", False),
        "exclusion_reason": liability.get("exclusion_reason") or "",
        "description": liability.get("description") or ""
    }
