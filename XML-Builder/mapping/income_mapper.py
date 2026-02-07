"""
Income Mapper
Maps incomes table data to MISMO INCOME fields
"""
from . import enums
from typing import Dict


def map_income_type(db_value: str) -> str:
    """Map income_type to MISMO IncomeType"""
    if not db_value:
        return "Base"
    return enums.INCOME_TYPE.get(db_value.upper(), db_value)


def map_income_source(db_value: str) -> str:
    """Map income_source to MISMO source classification"""
    if not db_value:
        return "Employment"
    return enums.INCOME_SOURCE.get(db_value.upper(), db_value)


def format_monthly_amount(amount) -> str:
    """Format income amount for MISMO"""
    if amount is None:
        return "0"
    try:
        return str(float(amount))
    except (ValueError, TypeError):
        return "0"


def extract_income_details(income: Dict) -> Dict:
    """Extract all income details for MISMO"""
    return {
        "income_type": map_income_type(income.get("income_type")),
        "income_source": map_income_source(income.get("income_source")),
        "monthly_amount": format_monthly_amount(income.get("monthly_amount")),
        "include_in_qualification": income.get("include_in_qualification", True),
        "verified_amount": format_monthly_amount(income.get("verified_amount")),
        "description": income.get("description") or ""
    }
