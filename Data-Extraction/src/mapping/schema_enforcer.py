"""
Schema Enforcer — Ensures relational payload compliance with Supabase schema.

This module defines the required fields and constraints for each table
based on the production Supabase schema, and enforces them on the 
relational payload to ensure database-ready output.
"""

from typing import Any, Dict, List, Optional
from src.utils.logging import logger


# Schema definition based on SUPABASE/schema.sql
SCHEMA_DEFINITIONS = {
    "applications": {
        "required": ["loan_product_id", "status"],
        "defaults": {
            "loan_product_id": None,
            "status": "imported",
            "stage": "processing",
        }
    },
    "customers": {
        "required": ["customer_type"],
        "defaults": {
            "customer_type": "individual",
        }
    },
    "application_customers": {
        "required": ["application_id", "customer_id", "role"],
        "defaults": {
            "role": "Borrower",
        }
    },
    "employments": {
        "required": ["customer_id", "application_id", "employment_type", "employer_name", "start_date"],
        "defaults": {
            "employment_type": "W2",
            "start_date": None,
            "is_current": True,
        },
        "disallowed": ["metadata"],  # Fields not in schema
    },
    "incomes": {
        "required": ["customer_id", "application_id", "income_source", "income_type", "monthly_amount"],
        "defaults": {
            "income_source": "Employment",
            "include_in_qualification": True,
        }
    },
    "demographics": {
        "required": ["customer_id", "application_id", "collection_method"],
        "defaults": {
            "collection_method": "FaceToFace",
            "declined_to_provide": False,
        }
    },
    "residences": {
        "required": ["customer_id", "application_id", "residence_type", "street_address", "city", "state", "zip_code"],
        "defaults": {
            "residence_type": "Current",
            "city": None,
            "state": None,
            "zip_code": None,
            "country": "US",
        }
    },
    "assets": {
        "required": ["application_id", "asset_category", "asset_type", "cash_or_market_value"],
        "defaults": {
            "asset_category": "LiquidAsset",
            "asset_type": "CheckingAccount",
            "cash_or_market_value": 0,
            "is_gift_or_grant": False,
            "verification_status": "not_verified",
        }
    },
    "liabilities": {
        "required": ["application_id", "liability_type", "monthly_payment"],
        "defaults": {
            "liability_type": "Other",
            "monthly_payment": 0,
            "to_be_paid_off_at_closing": False,
            "will_be_subordinated": False,
            "exclude_from_dti": False,
        }
    },
    "properties": {
        "required": [],
        "defaults": {}
    },
    "gift_funds": {
        "required": ["application_id", "customer_id", "donor_name", "gift_amount"],
        "defaults": {
            "gift_letter_received": False,
            "deposited": False,
        }
    },
    "declarations": {
        "required": ["customer_id", "application_id"],
        "defaults": {}
    },
    "real_estate_owned": {
        "required": ["customer_id", "application_id", "property_street_address", "property_city", "property_state", "property_zip_code"],
        "defaults": {
            "property_country": "US",
            "has_mortgage": False,
            "has_heloc": False,
            "is_rental": False,
        }
    },
}


class SchemaEnforcer:
    """Enforces Supabase schema compliance on relational payloads."""

    def __init__(self, schema_defs: Optional[Dict] = None):
        """Initialize with schema definitions.
        
        Args:
            schema_defs: Optional custom schema definitions. Defaults to SCHEMA_DEFINITIONS.
        """
        self.schema_defs = schema_defs or SCHEMA_DEFINITIONS

    def enforce(self, relational_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Enforce schema compliance on a relational payload.
        
        This ensures:
        1. All required fields are present (add with None/defaults if missing)
        2. Disallowed fields are removed
        3. Default values are applied where appropriate
        
        Args:
            relational_payload: The relational payload dict from RelationalTransformer
            
        Returns:
            The schema-compliant payload
        """
        enforced_payload = relational_payload.copy()
        
        for table_name, rows in relational_payload.items():
            # Skip metadata
            if table_name.startswith("_"):
                continue
                
            # Skip if not a list (shouldn't happen)
            if not isinstance(rows, list):
                continue
                
            # Skip if no schema definition for this table
            if table_name not in self.schema_defs:
                logger.debug(f"No schema definition for table: {table_name}")
                continue
            
            schema_def = self.schema_defs[table_name]
            required_fields = schema_def.get("required", [])
            defaults = schema_def.get("defaults", {})
            disallowed = schema_def.get("disallowed", [])
            
            # Process each row
            enforced_rows = []
            for row in rows:
                enforced_row = self._enforce_row(
                    row, 
                    required_fields, 
                    defaults, 
                    disallowed,
                    table_name
                )
                enforced_rows.append(enforced_row)
            
            enforced_payload[table_name] = enforced_rows
        
        logger.info("Schema enforcement complete - payload is database-ready")
        return enforced_payload

    def _enforce_row(
        self, 
        row: Dict[str, Any], 
        required_fields: List[str], 
        defaults: Dict[str, Any],
        disallowed: List[str],
        table_name: str
    ) -> Dict[str, Any]:
        """Enforce schema on a single row.
        
        Args:
            row: The row dict
            required_fields: List of required field names
            defaults: Dict of default values
            disallowed: List of disallowed field names
            table_name: Name of the table (for logging)
            
        Returns:
            Schema-compliant row
        """
        enforced_row = row.copy()
        
        # Remove disallowed fields
        for field in disallowed:
            if field in enforced_row:
                logger.debug(f"Removing disallowed field '{field}' from {table_name}")
                del enforced_row[field]
        
        # Add required fields that are missing
        for field in required_fields:
            # Skip reference fields (internal keys for FK resolution)
            if field.endswith("_id") and f"_{field.replace('_id', '_ref')}" in enforced_row:
                continue
                
            if field not in enforced_row:
                # Use default if available, otherwise None
                default_value = defaults.get(field)
                enforced_row[field] = default_value
                logger.debug(f"Added missing required field '{field}' to {table_name} with value: {default_value}")
        
        # Apply defaults for optional fields if not present
        for field, default_value in defaults.items():
            if field not in enforced_row and field not in required_fields:
                enforced_row[field] = default_value
        
        return enforced_row
