"""
Versioning Service
==================

Core logic for the append-only versioning system.
Handles the universal update algorithm for all versioned entities.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from supabase import Client

class VersioningService:
    """
    Universal service for managing versioned entities.
    Implements the core append-only logic.
    """
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
    
    def upsert_versioned_entity(
        self, 
        table: str, 
        logical_identity_fields: List[str], 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Universal upsert method for versioned entities.
        
        Algorithm:
        1. Find the current version (is_current=true) matching the logical identity
        2. If found -> "Update" (Insert new version, expire old one)
        3. If not found -> "Insert" (Create version 1)
        
        Args:
            table: Database table name
            logical_identity_fields: Fields that define the logical identity (e.g., ['customer_id', 'income_type'])
            data: The entity data provided in the payload
            
        Returns:
            Dictionary containing result metadata (version_number, is_update, record)
        """
        # Step 1: Construct the query for logical identity
        query = self.supabase.table(table).select("*").eq("is_current", True)
        
        # Add filters for each field in the logical identity
        identity_match = True
        for field in logical_identity_fields:
            if field in data:
                query = query.eq(field, data[field])
            else:
                # If a required identity field is missing, we can't match logic identity.
                # In strict mode this might error, but here we assume it's a new insert or validation failed earlier.
                identity_match = False
                break
        
        existing_record = None
        if identity_match:
            response = query.execute()
            if response.data and len(response.data) > 0:
                existing_record = response.data[0]
        
        now = datetime.now(timezone.utc).isoformat()
        
        if existing_record:
            # === UPDATE PATH (New Version) ===
            
            # 1. Expire the old record
            self.supabase.table(table).update({
                "is_current": False,
                "valid_to": now
            }).eq("id", existing_record["id"]).execute()
            
            # 2. Prepare new record data
            new_record_data = data.copy()
            new_record_data["version_number"] = existing_record["version_number"] + 1
            new_record_data["is_current"] = True
            new_record_data["valid_from"] = now
            new_record_data["valid_to"] = None
            
            # 3. Insert new version
            insert_response = self.supabase.table(table).insert(new_record_data).execute()
            new_record = insert_response.data[0]
            
            return {
                "success": True,
                "operation": "update",
                "is_update": True,
                "version_number": new_record["version_number"],
                "record": new_record
            }
            
        else:
            # === INSERT PATH (First Version) ===
            
            # 1. Prepare new record data
            new_record_data = data.copy()
            new_record_data["version_number"] = 1
            new_record_data["is_current"] = True
            new_record_data["valid_from"] = now
            new_record_data["valid_to"] = None
            
            # 2. Insert new version
            insert_response = self.supabase.table(table).insert(new_record_data).execute()
            new_record = insert_response.data[0]
            
            return {
                "success": True,
                "operation": "insert",
                "is_update": False,
                "version_number": 1,
                "record": new_record
            }
