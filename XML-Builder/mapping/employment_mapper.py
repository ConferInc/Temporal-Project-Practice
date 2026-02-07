"""
Employment Mapper
Maps employments table data to MISMO EMPLOYMENT fields
"""
from . import enums
from typing import Dict
from datetime import date


def map_employment_type(db_value: str) -> str:
    """Map employment_type to MISMO EmploymentClassificationType"""
    if not db_value:
        return "Employed"
    return enums.EMPLOYMENT_TYPE.get(db_value.upper(), "Employed")


def format_employer_address(employment: Dict) -> Dict[str, str]:
    """Extract employer address components"""
    return {
        "street": employment.get("employer_street_address") or "",
        "unit": employment.get("employer_unit") or "",
        "city": employment.get("employer_city") or "",
        "state": employment.get("employer_state") or "",
        "zip": employment.get("employer_zip_code") or ""
    }


def calculate_employment_months(start_date, end_date=None) -> int:
    """Calculate employment duration in months"""
    if not start_date:
        return 0
    
    try:
        if isinstance(start_date, str):
            start = date.fromisoformat(start_date)
        else:
            start = start_date
            
        if end_date:
            if isinstance(end_date, str):
                end = date.fromisoformat(end_date)
            else:
                end = end_date
        else:
            end = date.today()
            
        months = (end.year - start.year) * 12 + (end.month - start.month)
        return max(0, months)
    except (ValueError, AttributeError):
        return 0


def extract_employment_details(employment: Dict) -> Dict:
    """Extract all employment details for MISMO"""
    return {
        "employment_type": map_employment_type(employment.get("employment_type")),
        "is_current": employment.get("is_current", False),
        "employer_name": employment.get("employer_name") or "",
        "employer_phone": employment.get("employer_phone") or "",
        "employer_address": format_employer_address(employment),
        "position_title": employment.get("position_title") or "",
        "start_date": employment.get("start_date"),
        "end_date": employment.get("end_date"),
        "months_employed": calculate_employment_months(
            employment.get("start_date"),
            employment.get("end_date")
        ),
        "is_self_employed": employment.get("is_self_employed", False),
        "ownership_percentage": employment.get("ownership_percentage") or "",
        "self_employed_monthly_income": employment.get("self_employed_monthly_income") or 0
    }
