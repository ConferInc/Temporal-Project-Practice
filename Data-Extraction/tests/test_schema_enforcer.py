"""
Tests for Schema Enforcer
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.mapping.schema_enforcer import SchemaEnforcer


def test_schema_enforcer_adds_required_fields():
    """Test that enforcer adds missing required fields."""
    enforcer = SchemaEnforcer()
    
    # Create a minimal payload
    payload = {
        "_metadata": {"source": "test"},
        "applications": [
            {
                "_ref": "app_0",
                "_operation": "upsert",
                "status": "imported",
                # Missing loan_product_id (required)
            }
        ],
        "employments": [
            {
                "_ref": "emp_0",
                "_operation": "insert",
                "_customer_ref": "cust_0",
                "_application_ref": "app_0",
                "employment_type": "W2",
                "employer_name": "Test Corp",
                # Missing start_date (required)
            }
        ],
        "residences": [
            {
                "_ref": "res_0",
                "_operation": "insert",
                "_customer_ref": "cust_0",
                "_application_ref": "app_0",
                "residence_type": "Current",
                "street_address": "123 Main St",
                # Missing city, state, zip_code (all required)
            }
        ],
    }
    
    # Enforce schema
    enforced = enforcer.enforce(payload)
    
    # Check applications
    assert "loan_product_id" in enforced["applications"][0], "loan_product_id should be added"
    
    # Check employments
    assert "start_date" in enforced["employments"][0], "start_date should be added"
    
    # Check residences
    assert "city" in enforced["residences"][0], "city should be added"
    assert "state" in enforced["residences"][0], "state should be added"
    assert "zip_code" in enforced["residences"][0], "zip_code should be added"
    
    print("[PASS] Schema enforcer adds required fields correctly")


def test_schema_enforcer_removes_disallowed_fields():
    """Test that enforcer removes disallowed fields."""
    enforcer = SchemaEnforcer()
    
    payload = {
        "_metadata": {"source": "test"},
        "employments": [
            {
                "_ref": "emp_0",
                "_operation": "insert",
                "_customer_ref": "cust_0",
                "_application_ref": "app_0",
                "employment_type": "W2",
                "employer_name": "Test Corp",
                "start_date": None,
                "metadata": {  # This field is not in schema
                    "employer_ein": "12-3456789"
                }
            }
        ],
    }
    
    # Enforce schema
    enforced = enforcer.enforce(payload)
    
    # Check that metadata was removed
    assert "metadata" not in enforced["employments"][0], "metadata should be removed"
    
    print("[PASS] Schema enforcer removes disallowed fields correctly")


def test_schema_enforcer_applies_defaults():
    """Test that enforcer applies default values."""
    enforcer = SchemaEnforcer()
    
    payload = {
        "_metadata": {"source": "test"},
        "assets": [
            {
                "_ref": "asset_0",
                "_operation": "insert",
                "_application_ref": "app_0",
                # Missing many fields with defaults
            }
        ],
    }
    
    # Enforce schema
    enforced = enforcer.enforce(payload)
    
    asset = enforced["assets"][0]
    
    # Check defaults
    assert asset.get("asset_category") == "LiquidAsset", "Default asset_category should be applied"
    assert asset.get("asset_type") == "CheckingAccount", "Default asset_type should be applied"
    assert asset.get("cash_or_market_value") == 0, "Default cash_or_market_value should be applied"
    assert asset.get("is_gift_or_grant") == False, "Default is_gift_or_grant should be applied"
    
    print("[PASS] Schema enforcer applies defaults correctly")


if __name__ == "__main__":
    test_schema_enforcer_adds_required_fields()
    test_schema_enforcer_removes_disallowed_fields()
    test_schema_enforcer_applies_defaults()
    print("\n[SUCCESS] All schema enforcer tests passed!")
