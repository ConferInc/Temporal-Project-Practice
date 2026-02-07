"""
Customer Mapper
Maps customers table data to MISMO PARTY/BORROWER fields
"""
from . import enums
from typing import Dict, Optional
import json


def map_customer_type(db_value: str) -> str:
    """Map customer_type to MISMO party type"""
    if not db_value:
        return "Individual"
    return enums.CUSTOMER_TYPE.get(db_value.upper(), "Individual")


def map_borrower_role(db_value: str) -> str:
    """Map application_customers.role to MISMO RoleType"""
    if not db_value:
        return "Borrower"
    return enums.BORROWER_ROLE.get(db_value.upper(), "Borrower")


def map_marital_status(db_value: str) -> str:
    """Map marital_status to MISMO MaritalStatusType"""
    if not db_value:
        return ""
    return enums.MARITAL_STATUS.get(db_value.upper(), db_value)


def map_citizenship_type(db_value: str) -> str:
    """Map citizenship_type to MISMO CitizenshipResidencyType"""
    if not db_value:
        return ""
    return enums.CITIZENSHIP_TYPE.get(db_value.upper(), db_value)


def parse_customer_name(customer: Dict) -> Dict[str, str]:
    """
    Extract name components from customer record
    Returns dict with first_name, middle_name, last_name, suffix
    """
    return {
        "first_name": customer.get("first_name") or "",
        "middle_name": customer.get("middle_name") or "",
        "last_name": customer.get("last_name") or "",
        "suffix": customer.get("suffix") or "",
        "company_name": customer.get("company_name") or ""
    }


def parse_addresses(addresses_jsonb: Optional[str]) -> list:
    """
    Parse JSONB addresses field into list of address dicts
    Expected structure: [{"type": "current", "street": "...", "city": "...", ...}]
    """
    if not addresses_jsonb:
        return []
    
    try:
        if isinstance(addresses_jsonb, str):
            addresses = json.loads(addresses_jsonb)
        else:
            addresses = addresses_jsonb
            
        if not isinstance(addresses, list):
            return []
            
        return addresses
    except (json.JSONDecodeError, TypeError):
        return []


def get_current_address(customer: Dict) -> Optional[Dict]:
    """Extract current/primary address from customer addresses JSONB"""
    addresses = parse_addresses(customer.get("addresses"))
    
    # Look for current address
    for addr in addresses:
        if addr.get("type") == "current" or addr.get("is_current"):
            return addr
    
    # Fallback to first address
    return addresses[0] if addresses else None


def format_phone(phone: str) -> str:
    """Format phone number for MISMO (remove non-digits if needed)"""
    if not phone:
        return ""
    # Keep as-is for now, can add formatting logic if needed
    return phone


def extract_contact_info(customer: Dict) -> Dict[str, str]:
    """Extract all contact information"""
    return {
        "email": customer.get("email") or "",
        "phone": customer.get("phone") or "",
        "phone_home": customer.get("phone_home") or "",
        "phone_cell": customer.get("phone_cell") or "",
        "phone_work": customer.get("phone_work") or "",
        "phone_work_ext": customer.get("phone_work_ext") or ""
    }
