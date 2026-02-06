"""
User Service
============

Handles user entity operations (non-versioned reference table).
"""

from typing import Dict, Any
from supabase import Client


class UserService:
    """Service for managing user entities (non-versioned)."""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.table = "users"
    
    def upsert_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upsert a user record (insert or update based on email).
        
        Args:
            data: User data with email, organization_id, and optionally id
            
        Returns:
            Dictionary with upserted user record
        """
        email = data.get("email")
        if not email:
            raise ValueError("Email is required for user upsert")
        
        # Check if user exists by email
        existing_user = self.supabase.table(self.table).select("*").eq("email", email).execute()
        
        if existing_user.data and len(existing_user.data) > 0:
            # Update existing user
            user_id = existing_user.data[0]["id"]
            update_data = {k: v for k, v in data.items() if k != "id"}
            
            result = self.supabase.table(self.table).update(update_data).eq("id", user_id).execute()
            
            return {
                "record": result.data[0] if result.data else None,
                "is_update": True,
                "version_number": None  # Users are not versioned
            }
        else:
            # Insert new user
            insert_data = {k: v for k, v in data.items() if k in ["email", "organization_id", "id"]}
            result = self.supabase.table(self.table).insert(insert_data).execute()
            
            return {
                "record": result.data[0] if result.data else None,
                "is_update": False,
                "version_number": None  # Users are not versioned
            }
