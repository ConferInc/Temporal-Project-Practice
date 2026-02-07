"""
Data Fetchers for MISMO XML Generation
Fetches data from Supabase database using the comprehensive schema
"""
from typing import Dict, Any, List
from db.supabase_client import supabase


def get_application(application_id: str) -> Dict[str, Any]:
    """Fetch application details by ID"""
    response = supabase.table("applications").select("*").eq("id", application_id).execute()
    if not response.data:
        raise ValueError(f"Application with ID {application_id} not found.")
    return response.data[0]


def get_customers(application_id: str) -> List[Dict[str, Any]]:
    """
    Fetch all customers linked to an application via application_customers junction table
    Returns customers with their role, sequence, and other junction table metadata
    """
    response = supabase.table("application_customers") \
        .select("*, customers(*)") \
        .eq("application_id", application_id) \
        .order("sequence") \
        .execute()
    
    # Flatten the result
    customers_list = []
    for item in response.data:
        customer_data = item.get("customers", {})
        # Merge junction data (role, sequence, ownership_percentage) with customer data
        customer = {
            **customer_data,
            "role": item.get("role"),
            "sequence": item.get("sequence"),
            "ownership_percentage": item.get("ownership_percentage"),
            "will_occupy_property": item.get("will_occupy_property"),
            "will_be_on_title": item.get("will_be_on_title")
        }
        customers_list.append(customer)
        
    return customers_list


def get_property(application_id: str) -> Dict[str, Any]:
    """
    Fetch property linked to application via applications.property_id
    """
    # First get the application to find property_id
    app = get_application(application_id)
    property_id = app.get("property_id")
    
    if not property_id:
        return {}
    
    response = supabase.table("properties").select("*").eq("id", property_id).execute()
    if not response.data:
        return {}
    
    return response.data[0]


def get_employments(customer_id: str, application_id: str = None) -> List[Dict[str, Any]]:
    """Fetch employments for a customer"""
    query = supabase.table("employments").select("*").eq("customer_id", customer_id)
    
    # Optionally filter by application_id if provided
    if application_id:
        query = query.eq("application_id", application_id)
    
    response = query.execute()
    return response.data


def get_incomes(customer_id: str, application_id: str = None) -> List[Dict[str, Any]]:
    """Fetch incomes for a customer"""
    query = supabase.table("incomes").select("*").eq("customer_id", customer_id)
    
    # Optionally filter by application_id if provided
    if application_id:
        query = query.eq("application_id", application_id)
    
    response = query.execute()
    return response.data


def get_assets(application_id: str) -> List[Dict[str, Any]]:
    """
    Fetch assets for an application with ownership information
    """
    response = supabase.table("assets") \
        .select("*, asset_ownership(*)") \
        .eq("application_id", application_id) \
        .execute()
    
    return response.data


def get_liabilities(application_id: str) -> List[Dict[str, Any]]:
    """
    Fetch liabilities for an application with ownership information
    """
    response = supabase.table("liabilities") \
        .select("*, liability_ownership(*)") \
        .eq("application_id", application_id) \
        .execute()
    
    return response.data


def fetch_loan_data(application_id: str) -> Dict[str, Any]:
    """
    Orchestrates fetching all data for a complete loan file
    Returns a dictionary structured by entity type
    """
    try:
        # Fetch application
        application = get_application(application_id)
        
        # Fetch customers with their roles
        customers = get_customers(application_id)
        
        # Enrich each customer with their financial data
        for customer in customers:
            customer_id = customer.get("id")
            customer["employments"] = get_employments(customer_id, application_id)
            customer["incomes"] = get_incomes(customer_id, application_id)
        
        # Fetch property
        property_data = get_property(application_id)
        
        # Fetch assets and liabilities (application-level)
        assets = get_assets(application_id)
        liabilities = get_liabilities(application_id)

        return {
            "application": application,
            "customers": customers,
            "property": property_data,
            "assets": assets,
            "liabilities": liabilities
        }
    except Exception as e:
        print(f"Error fetching loan data: {e}")
        raise
