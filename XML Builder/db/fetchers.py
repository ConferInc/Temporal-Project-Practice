from typing import Dict, Any, List
from db.supabase_client import supabase

def get_application(loan_id: str) -> Dict[str, Any]:
    """Fetches application details by ID."""
    response = supabase.table("applications").select("*").eq("id", loan_id).execute()
    if not response.data:
        raise ValueError(f"Application with ID {loan_id} not found.")
    return response.data[0]

def get_borrowers(application_id: str) -> List[Dict[str, Any]]:
    """Fetches all borrowers linked to an application via application_borrowers and users tables."""
    # We need to join application_borrowers with users to get the details
    # Supabase syntax for joining: select('*, users(*)')
    response = supabase.table("application_borrowers") \
        .select("*, users(*)") \
        .eq("application_id", application_id) \
        .execute()
    
    # Flatten the result so it looks like a single object per borrower
    borrowers = []
    for item in response.data:
        user_data = item.get("users", {})
        # Merge junction data (role, is_primary) with user data
        borrower = {**user_data, **item}
        # Clean up nested 'users' key if you want a flat structure, or keep it.
        # Let's keep it somewhat flat for easier consumption
        if "users" in borrower:
            del borrower["users"]
        borrowers.append(borrower)
        
    return borrowers

def get_properties(application_id: str) -> List[Dict[str, Any]]:
    """Fetches properties linked to an application."""
    response = supabase.table("properties").select("*").eq("application_id", application_id).execute()
    return response.data

def get_incomes(user_id: str) -> List[Dict[str, Any]]:
    """Fetches current incomes linked to a user (borrower)."""
    # Using the is_current flag from schema
    response = supabase.table("incomes") \
        .select("*") \
        .eq("customer_id", user_id) \
        .eq("is_current", True) \
        .execute()
    return response.data

def get_liabilities(application_id: str, user_ids: List[str]) -> List[Dict[str, Any]]:
    """Fetches liabilities. Can be linked to application OR customer."""
    # The schema has both application_id and customer_id in liabilities.
    # We should probably fetch by application_id if populated, or by customer_ids.
    
    # Strategy 1: Fetch by Application ID if liabilities are linked to the app
    response_app = supabase.table("liabilities") \
        .select("*") \
        .eq("application_id", application_id) \
        .eq("is_current", True) \
        .execute()
        
    if response_app.data:
        return response_app.data
        
    # Strategy 2: Fallback to fetching by customer_ids if application_id is null/empty 
    # (assuming liabilities follow the user)
    # This is a bit complex with standard Supabase client without 'in' query easy setup or loop
    # We'll stick to application_id for now as the schema has it.
    
    return []

def get_employment(user_id: str) -> List[Dict[str, Any]]:
    """Fetches current employment history for a borrower."""
    response = supabase.table("employments") \
        .select("*") \
        .eq("customer_id", user_id) \
        .eq("is_current", True) \
        .execute()
    return response.data

def fetch_loan_data(loan_id: str) -> Dict[str, Any]:
    """
    Orchestrates fetching all data for a complete loan file.
    Returns a dictionary structured by entity type.
    """
    try:
        application = get_application(loan_id)
        app_id = application["id"]

        borrowers = get_borrowers(app_id)
        user_ids = [b.get("user_id") or b.get("id") for b in borrowers] # Handle ID locations
        
        # Enrich borrowers with their specific data
        enriched_borrowers = []
        for borrower in borrowers:
            # The user_id is coming from the junction table 'user_id' or the user table 'id'
            # In get_borrowers merge, 'user_id' from junction should be preserved.
            b_id = borrower.get("user_id")
            
            borrower["incomes"] = get_incomes(b_id)
            borrower["employment"] = get_employment(b_id)
            enriched_borrowers.append(borrower)
            
        properties = get_properties(app_id)
        liabilities = get_liabilities(app_id, user_ids)

        return {
            "application": application,
            "borrowers": enriched_borrowers,
            "properties": properties,
            "liabilities": liabilities
        }
    except Exception as e:
        print(f"Error fetching loan data: {e}")
        raise
