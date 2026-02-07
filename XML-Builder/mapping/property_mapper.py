"""
Property Mapper
Maps properties table data to MISMO PROPERTY fields
"""
from . import enums
from typing import Dict, Optional
import json


def map_property_type(db_value: str) -> str:
    """Map property_type to MISMO PropertyType"""
    if not db_value:
        return ""
    return enums.PROPERTY_TYPE.get(db_value.upper(), db_value)


def parse_property_address(address_jsonb: Optional[str]) -> Dict[str, str]:
    """
    Parse JSONB address field from properties table
    Expected structure: {"street": "...", "city": "...", "state": "...", "zip": "..."}
    """
    if not address_jsonb:
        return {
            "street": "",
            "unit": "",
            "city": "",
            "state": "",
            "zip": "",
            "country": "US"
        }
    
    try:
        if isinstance(address_jsonb, str):
            addr = json.loads(address_jsonb)
        else:
            addr = address_jsonb
            
        return {
            "street": addr.get("street") or addr.get("address_line") or "",
            "unit": addr.get("unit") or addr.get("unit_number") or "",
            "city": addr.get("city") or "",
            "state": addr.get("state") or "",
            "zip": addr.get("zip") or addr.get("zip_code") or addr.get("postal_code") or "",
            "country": addr.get("country") or "US"
        }
    except (json.JSONDecodeError, TypeError):
        return {
            "street": "",
            "unit": "",
            "city": "",
            "state": "",
            "zip": "",
            "country": "US"
        }


def extract_property_details(property_data: Dict) -> Dict:
    """Extract all property details for MISMO"""
    address = parse_property_address(property_data.get("address"))
    
    return {
        "address": address,
        "property_type": map_property_type(property_data.get("property_type")),
        "year_built": property_data.get("year_built") or "",
        "square_feet": property_data.get("square_feet") or "",
        "bedrooms": property_data.get("bedrooms") or "",
        "bathrooms": property_data.get("bathrooms") or "",
        "appraised_value": property_data.get("appraised_value") or "",
        "purchase_price": property_data.get("purchase_price") or ""
    }


def format_state_code(state: str) -> str:
    """Ensure state is 2-letter code"""
    if not state:
        return ""
    
    # If already 2 letters, return as-is
    if len(state) == 2:
        return state.upper()
    
    # Try to map from full name
    return enums.STATE_CODES.get(state.upper(), state)
