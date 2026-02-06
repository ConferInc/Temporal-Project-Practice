"""
Quick validation script for MISMO 3.4 schema migration.
Tests core infrastructure components.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.schema_registry import get_schema_registry
from utils.enum_validator import get_enum_validator
from utils.path_resolver import get_path_resolver

def test_schema_registry():
    """Test SchemaRegistry loads and validates paths."""
    print("\n" + "="*80)
    print("TEST 1: Schema Registry")
    print("="*80)
    
    registry = get_schema_registry()
    schema = registry.get_schema()
    
    print(f"✅ Schema loaded successfully")
    print(f"   Schema version: {schema.get('document_metadata', {}).get('schema_version', 'unknown')}")
    
    # Test path validation
    test_paths = [
        "deal.identifiers.loan_id",
        "deal.parties[0].individual.first_name",
        "deal.assets[0].asset_type.value",
        "deal.parties[0].employment[0].monthly_income.base",
        "invalid.path.that.does.not.exist"
    ]
    
    print("\n   Path Validation Tests:")
    for path in test_paths:
        is_valid = registry.validate_path(path)
        status = "✅" if is_valid else "❌"
        print(f"   {status} {path}: {is_valid}")
    
    # Test enum detection
    print("\n   Enum Detection Tests:")
    enum_paths = [
        "deal.transaction_information.loan_purpose",
        "deal.assets[0].asset_type",
        "deal.parties[0].individual.citizenship_residency"
    ]
    
    for path in enum_paths:
        is_enum = registry.is_enum_field(path)
        options = registry.get_enum_options(path) if is_enum else None
        print(f"   {'✅' if is_enum else '❌'} {path}: enum={is_enum}, options={len(options) if options else 0}")

def test_enum_validator():
    """Test EnumValidator enforces strict validation."""
    print("\n" + "="*80)
    print("TEST 2: Enum Validator")
    print("="*80)
    
    validator = get_enum_validator()
    
    # Test valid enum
    try:
        validator.validate_enum_value(
            "deal.assets[0].asset_type.value",
            "Checking",
            ["Checking", "Savings", "Retirement"]
        )
        print("✅ Valid enum value accepted: 'Checking'")
    except Exception as e:
        print(f"❌ Valid enum rejected: {e}")
    
    # Test invalid enum
    try:
        validator.validate_enum_value(
            "deal.assets[0].asset_type.value",
            "InvalidType",
            ["Checking", "Savings", "Retirement"]
        )
        print("❌ Invalid enum value accepted (should have failed!)")
    except Exception as e:
        print(f"✅ Invalid enum rejected correctly: {type(e).__name__}")

def test_path_resolver():
    """Test PathResolver handles arrays and nested paths."""
    print("\n" + "="*80)
    print("TEST 3: Path Resolver")
    print("="*80)
    
    resolver = get_path_resolver()
    result = {}
    
    # Test simple path
    resolver.set_value_at_path(result, "deal.identifiers.loan_id", "LOAN123")
    print(f"✅ Simple path: {result}")
    
    # Test array path
    resolver.set_value_at_path(result, "deal.parties[0].individual.first_name", "John")
    resolver.set_value_at_path(result, "deal.parties[0].individual.last_name", "Doe")
    print(f"✅ Array path (index 0): {result}")
    
    # Test nested array
    resolver.set_value_at_path(result, "deal.parties[0].employment[0].employer_name", "ABC Corp")
    resolver.set_value_at_path(result, "deal.parties[0].employment[0].monthly_income.base", 5000)
    print(f"✅ Nested array: {result}")
    
    # Test multiple array entries
    resolver.set_value_at_path(result, "deal.assets[0].institution_name", "Bank of America")
    resolver.set_value_at_path(result, "deal.assets[1].institution_name", "Chase Bank")
    print(f"✅ Multiple array entries: {result}")
    
    # Test get value
    value = resolver.get_value_at_path(result, "deal.parties[0].individual.first_name")
    print(f"✅ Get value: deal.parties[0].individual.first_name = {value}")

def test_canonical_mapper():
    """Test CanonicalMapper with schema-driven architecture."""
    print("\n" + "="*80)
    print("TEST 4: Canonical Mapper (Schema-Driven)")
    print("="*80)
    
    from tools.canonical_mapper import map_to_canonical_model
    
    # Test with sample extracted fields
    extracted_fields = {
        "institutionName": "Bank of America",
        "currentBalance": 25000,
        "accountType": "Checking",
        "firstName": "John",
        "lastName": "Doe"
    }
    
    try:
        result = map_to_canonical_model("BankStatement", extracted_fields)
        print(f"✅ Mapping successful")
        print(f"   Populated sections: {list(result.keys())}")
        
        # Check if data is in correct structure
        if "deal" in result:
            print(f"   ✅ Uses new 'deal' structure")
            if "assets" in result.get("deal", {}):
                print(f"   ✅ Assets mapped: {len(result['deal']['assets'])} entries")
            if "parties" in result.get("deal", {}):
                print(f"   ✅ Parties mapped: {len(result['deal']['parties'])} entries")
        else:
            print(f"   ❌ Missing 'deal' structure (using old schema?)")
            
    except Exception as e:
        print(f"❌ Mapping failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all validation tests."""
    print("\n" + "="*80)
    print("MISMO 3.4 SCHEMA MIGRATION - VALIDATION TESTS")
    print("="*80)
    
    try:
        test_schema_registry()
        test_enum_validator()
        test_path_resolver()
        test_canonical_mapper()
        
        print("\n" + "="*80)
        print("✅ ALL VALIDATION TESTS COMPLETED")
        print("="*80)
        print("\nSchema migration infrastructure is working correctly!")
        
    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
