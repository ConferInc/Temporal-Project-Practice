"""
Centralized Mapping Layer
==========================

This module defines the canonical JSON contract and maps entity keys to database tables.

Purpose:
- Decouple canonical JSON from database schema
- Enable schema evolution without breaking the JSON contract
- Define logical identity for each entity type
"""

from typing import Dict, List, Any

# ============================================
# ENTITY TO TABLE MAPPING
# ============================================

ENTITY_COLUMN_MAP: Dict[str, Dict[str, Any]] = {
    "user": {
        "table": "users",
        "versioned": False,  # Users table is NOT versioned
        "columns": {
            "id": "id",
            "organization_id": "organization_id",
            "email": "email",
        },
        "logical_identity": ["email"],  # Used for upsert logic
    },
    "income": {
        "table": "incomes",
        "versioned": True,
        "columns": {
            "customer_id": "customer_id",
            "income_type": "income_type",
            "monthly_amount": "monthly_amount",
        },
        "logical_identity": ["customer_id", "income_type"],
    },
    "employment": {
        "table": "employments",
        "versioned": True,
        "columns": {
            "customer_id": "customer_id",
            "employer_name": "employer_name",
            "employment_type": "employment_type",
        },
        "logical_identity": ["customer_id", "employer_name"],
    },
    "asset": {
        "table": "assets",
        "versioned": True,
        "columns": {
            "customer_id": "customer_id",
            "application_id": "application_id",
            "asset_type": "asset_type",
            "asset_value": "asset_value",
        },
        "logical_identity": ["customer_id", "asset_type"],
    },
    "liability": {
        "table": "liabilities",
        "versioned": True,
        "columns": {
            "customer_id": "customer_id",
            "application_id": "application_id",
            "liability_type": "liability_type",
            "monthly_payment": "monthly_payment",
        },
        "logical_identity": ["customer_id", "liability_type"],
    },
}


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_table_name(entity_key: str) -> str:
    """Get database table name for a given entity key."""
    if entity_key not in ENTITY_COLUMN_MAP:
        raise ValueError(f"Unknown entity key: {entity_key}")
    return ENTITY_COLUMN_MAP[entity_key]["table"]


def is_versioned(entity_key: str) -> bool:
    """Check if an entity type is versioned."""
    if entity_key not in ENTITY_COLUMN_MAP:
        raise ValueError(f"Unknown entity key: {entity_key}")
    return ENTITY_COLUMN_MAP[entity_key]["versioned"]


def get_column_mapping(entity_key: str) -> Dict[str, str]:
    """Get column mapping for a given entity key."""
    if entity_key not in ENTITY_COLUMN_MAP:
        raise ValueError(f"Unknown entity key: {entity_key}")
    return ENTITY_COLUMN_MAP[entity_key]["columns"]


def get_logical_identity_fields(entity_key: str) -> List[str]:
    """Get logical identity fields for a given entity key."""
    if entity_key not in ENTITY_COLUMN_MAP:
        raise ValueError(f"Unknown entity key: {entity_key}")
    return ENTITY_COLUMN_MAP[entity_key]["logical_identity"]


def map_json_to_db(entity_key: str, json_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map canonical JSON fields to database column names.
    
    Args:
        entity_key: The top-level entity key (e.g., "income", "employment")
        json_data: The JSON data for this entity
        
    Returns:
        Dictionary with database column names as keys
    """
    if entity_key not in ENTITY_COLUMN_MAP:
        raise ValueError(f"Unknown entity key: {entity_key}")
    
    column_mapping = ENTITY_COLUMN_MAP[entity_key]["columns"]
    db_data = {}
    
    for json_field, db_column in column_mapping.items():
        if json_field in json_data:
            db_data[db_column] = json_data[json_field]
    
    return db_data


def get_supported_entities() -> List[str]:
    """Get list of all supported entity keys."""
    return list(ENTITY_COLUMN_MAP.keys())
