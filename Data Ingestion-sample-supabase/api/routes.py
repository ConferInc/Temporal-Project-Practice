"""
API Routes
==========

FastAPI routes for the versioned data platform.
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
from api.handlers import IngestionHandler

router = APIRouter()
handler = IngestionHandler()


@router.post("/ingest")
async def ingest_canonical_data(payload: Dict[str, Any] = Body(..., example={
    "income": {
        "customer_id": "123e4567-e89b-12d3-a456-426614174000",
        "income_type": "salary",
        "monthly_amount": 50000
    }
})):
    """
    Ingest canonical JSON data.
    
    Accepts a payload with one or more top-level entity keys.
    Each entity is processed independently with versioning logic applied.
    
    The canonical JSON format uses top-level keys to identify entity types:
    - "user" for user records
    - "income" for income records
    - "employment" for employment records
    - "asset" for asset records
    - "liability" for liability records
    
    Returns:
        Results for each entity processed, including version numbers and any errors
    """
    try:
        result = handler.process_payload(payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "versioned-data-platform"}
