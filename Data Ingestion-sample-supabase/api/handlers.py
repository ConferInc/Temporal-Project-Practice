"""
API Handlers
============

Request handling logic for canonical JSON ingestion.
"""

from typing import Dict, Any, List
from fastapi import HTTPException
from db.supabase_client import get_supabase_client
from mappings.entity_column_map import (
    map_json_to_db,
    get_supported_entities,
    is_versioned
)
from services.user_service import UserService
from services.income_service import IncomeService
from services.employment_service import EmploymentService
from services.asset_service import AssetService
from services.liability_service import LiabilityService


class IngestionHandler:
    """Handles multi-entity batch ingestion from canonical JSON."""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        
        # Initialize all services
        self.services = {
            "user": UserService(self.supabase),
            "income": IncomeService(self.supabase),
            "employment": EmploymentService(self.supabase),
            "asset": AssetService(self.supabase),
            "liability": LiabilityService(self.supabase),
        }
    
    def process_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a canonical JSON payload containing one or more entities.
        
        Args:
            payload: Canonical JSON with top-level entity keys
            
        Returns:
            Dictionary with results for each entity processed
        """
        results = []
        errors = []
        
        supported_entities = get_supported_entities()
        
        # Iterate over each top-level key in the payload
        for entity_key, entity_data in payload.items():
            try:
                # Validate entity key
                if entity_key not in supported_entities:
                    errors.append({
                        "entity": entity_key,
                        "error": f"Unknown entity type: {entity_key}"
                    })
                    continue
                
                # Map JSON to database columns
                db_data = map_json_to_db(entity_key, entity_data)
                
                # Route to appropriate service
                result = self._process_entity(entity_key, db_data)
                
                results.append({
                    "entity": entity_key,
                    "success": True,
                    "version_number": result.get("version_number"),
                    "is_update": result.get("is_update", False),
                    "record_id": result["record"]["id"] if result.get("record") else None
                })
                
            except Exception as e:
                errors.append({
                    "entity": entity_key,
                    "error": str(e)
                })
        
        return {
            "success": len(errors) == 0,
            "results": results,
            "errors": errors,
            "total_processed": len(results),
            "total_errors": len(errors)
        }
    
    def _process_entity(self, entity_key: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single entity using the appropriate service.
        
        Args:
            entity_key: Entity type (user, income, employment, etc.)
            data: Mapped database data
            
        Returns:
            Result from the service
        """
        if entity_key == "user":
            return self.services["user"].upsert_user(data)
        elif entity_key == "income":
            return self.services["income"].upsert_income(data)
        elif entity_key == "employment":
            return self.services["employment"].upsert_employment(data)
        elif entity_key == "asset":
            return self.services["asset"].upsert_asset(data)
        elif entity_key == "liability":
            return self.services["liability"].upsert_liability(data)
        else:
            raise ValueError(f"No service handler for entity: {entity_key}")
