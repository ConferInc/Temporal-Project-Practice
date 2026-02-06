"""
Income Service
==============

Handles income entity operations (versioned).
"""

from typing import Dict, Any
from supabase import Client
from services.versioning_service import VersioningService
from mappings.entity_column_map import get_table_name, get_logical_identity_fields


class IncomeService:
    """Service for managing income entities (versioned)."""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.versioning_service = VersioningService(supabase_client)
        self.table = get_table_name("income")
        self.logical_identity_fields = get_logical_identity_fields("income")
    
    def upsert_income(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upsert an income record (creates new version).
        
        Args:
            data: Income data with customer_id, income_type, monthly_amount
            
        Returns:
            Dictionary with version metadata
        """
        return self.versioning_service.upsert_versioned_entity(
            table=self.table,
            logical_identity_fields=self.logical_identity_fields,
            data=data
        )
