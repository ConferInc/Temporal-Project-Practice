
import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tools.unified_extraction import unified_extract
from utils.logging import logger

def main():
    file_name = "URLA LoanApplication_1---0001 filled.pdf"
    file_path = project_root / "Test_upload_files" / file_name
    
    print(f"Testing URLA Extraction on: {file_path}")
    
    if not file_path.exists():
        print("File not found!")
        return

    try:
        result = unified_extract(str(file_path))
        
        print("\n--- Extraction Result Summary ---")
        print(f"Classification: {result['classification']['document_category']}")
        
        canonical_data = result['canonical_data']
        print(f"\nCanonical Data Keys (Should match URLA Schema):")
        print(list(canonical_data.keys()))
        
        # Save output
        output_path = project_root / "output" / "urla_test_output.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(canonical_data, f, indent=2)
            
        print(f"\nSaved output to {output_path}")
        
        # Verify schema adherence (basic check)
        expected_keys = ["UniformResidentialLoanApplication"] 
        # or checking top level key if schema/urla.json has it.
        # schema/urla.json starts with { "UniformResidentialLoanApplication": ... }
        
        if "UniformResidentialLoanApplication" in canonical_data:
             print("✅ Success: Top level key matches URLA Schema")
             
             inner = canonical_data["UniformResidentialLoanApplication"]
             if "I_TypeOfMortgageAndTermsOfLoan" in inner:
                  print("✅ Success: Found Section I")
             else:
                  print("❌ Warning: Section I not found")
        else:
             print("❌ Failure: Top level key missing or incorrect")
             print(f"Actual top keys: {list(canonical_data.keys())}")

    except Exception as e:
        print(f"❌ Error caught in test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
