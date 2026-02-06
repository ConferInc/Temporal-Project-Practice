"""
Liability Service
=================

Handles liability entity operations (versioned).
"""

from typing import Dict, Any
from supabase import Client
from services.versioning_service import VersioningService
from mappings.entity_column_map import get_table_name, get_logical_identity_fields


class LiabilityService:
    """Service for managing liability entities (versioned)."""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.versioning_service = VersioningService(supabase_client)
        self.table = get_table_name("liability")
        self.logical_identity_fields = get_logical_identity_fields("liability")
    
    def upsert_liability(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upsert a liability record (creates new version).
        
        Args:
            data: Liability data with customer_id, liability_type, monthly_payment, and optionally application_id
            
        Returns:
            Dictionary with version metadata
        """
        return self.versioning_service.upsert_versioned_entity(
            table=self.table,
            logical_identity_fields=self.logical_identity_fields,
            data=data
        )
