"""
Asset Service
=============

Handles asset entity operations (versioned).
"""

from typing import Dict, Any
from supabase import Client
from services.versioning_service import VersioningService
from mappings.entity_column_map import get_table_name, get_logical_identity_fields


class AssetService:
    """Service for managing asset entities (versioned)."""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.versioning_service = VersioningService(supabase_client)
        self.table = get_table_name("asset")
        self.logical_identity_fields = get_logical_identity_fields("asset")
    
    def upsert_asset(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upsert an asset record (creates new version).
        
        Args:
            data: Asset data with customer_id, asset_type, asset_value, and optionally application_id
            
        Returns:
            Dictionary with version metadata
        """
        return self.versioning_service.upsert_versioned_entity(
            table=self.table,
            logical_identity_fields=self.logical_identity_fields,
            data=data
        )
