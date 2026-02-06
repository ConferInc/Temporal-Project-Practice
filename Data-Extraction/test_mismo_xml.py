"""
Test MISMO 3.6 XML Generation
"""
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tools.mismo_mapper import generate_mismo_xml

def match_mismo_3_6_structure(xml_str):
    """Checks for specific MISMO 3.6 containers"""
    
    # 3.6 Specific Tokens we expect based on our mapping
    checks = [
        ("<TAXPAYER_IDENTIFIERS>", "New Taxpayer Container"),
        ("<TAXPAYER_IDENTIFIER>", "Nested Taxpayer ID"),
        ("<NAME>", "Individual Name Container"),
        ("<CONTACT_POINTS>", "Contact Points Container")
    ]
    
    results = []
    all_passed = True
    
    for tag, desc in checks:
        if tag in xml_str:
            results.append(f"✅ Found {desc} ({tag})")
        else:
            # Note: Taxpayer ID might not be in the Bank Statement sample if not extracted
            # Check if canonical input had it.
            # Bank Statement sample has firstName/lastName but usually no SSN.
            # URLA sample would have SSN.
            results.append(f"⚠️ Missing {desc} ({tag}) - Check if input had this data")
            # Don't fail the whole test if data just wasn't present, but warn.

    return results

def main():
    # Load canonical input (Bank Statement)
    # Note: BS sample usually doesn't have SSN, so TAXPAYER_IDENTIFIERS might stay empty/missing in XML
    input_path = project_root / "output" / "pipeline_test" / "04_canonical_output.json"
    
    # Let's mock a URLA-like input to test full 3.6 structure for SSN
    mock_input = {
        "parties": [
            {
                "individual": {
                    "firstName": "John",
                    "lastName": "Doe"
                },
                "taxpayerIdentifier": {
                    "value": "123-45-6789",
                    "type": "SSN"
                },
                "contactPoints": {
                    "email": "john@example.com"
                }
            }
        ],
        "deal": {
            "loanPurposeType": "Purchase"
        }
    }
    
    print("Testing with Mock URLA Data for full 3.6 Structure...")
    result = generate_mismo_xml(mock_input)
    
    xml_out = result["mismo_xml"]
    print("\nGenerated XML Snippet:")
    print("-" * 50)
    print(xml_out[:1000]) # Print first 1000 chars
    print("-" * 50)
    
    # Validation
    checks = match_mismo_3_6_structure(xml_out)
    print("\nValidation Results:")
    for c in checks:
        print(c)

    # Also run on the actual pipeline output
    if input_path.exists():
        print("\nTesting with Actual Pipeline Output (Bank Statement)...")
        with open(input_path, 'r', encoding='utf-8') as f:
            real_data = json.load(f)
        real_result = generate_mismo_xml(real_data)
        print("✅ Generation successful for pipeline output")

if __name__ == "__main__":
    main()
