"""
Employment Service
==================

Handles employment entity operations (versioned).
"""

from typing import Dict, Any
from supabase import Client
from services.versioning_service import VersioningService
from mappings.entity_column_map import get_table_name, get_logical_identity_fields


class EmploymentService:
    """Service for managing employment entities (versioned)."""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.versioning_service = VersioningService(supabase_client)
        self.table = get_table_name("employment")
        self.logical_identity_fields = get_logical_identity_fields("employment")
    
    def upsert_employment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upsert an employment record (creates new version).
        
        Args:
            data: Employment data with customer_id, employer_name, employment_type
            
        Returns:
            Dictionary with version metadata
        """
        return self.versioning_service.upsert_versioned_entity(
            table=self.table,
            logical_identity_fields=self.logical_identity_fields,
            data=data
        )
