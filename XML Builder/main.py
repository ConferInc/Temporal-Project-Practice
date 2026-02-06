import sys
import os
import argparse
from db import fetchers
from domain.loan_snapshot import LoanSnapshot
from validation import loan_validator
from xml_gen.xml_builder import build_mismo_xml

def main():
    parser = argparse.ArgumentParser(description="Generate MISMO XML from Supabase Loan Data")
    parser.add_argument("loan_id", help="The UUID of the loan application to process")
    parser.add_argument("--output", help="Output filename", default=None)
    
    args = parser.parse_args()
    
    # Determine output filename
    if args.output:
        output_path = args.output
    else:
        output_path = os.path.join("output", f"{args.loan_id}_mismo.xml")

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        print(f"Fetching data for loan ID: {args.loan_id}...")
        # 1. Fetch Data
        raw_data = fetchers.fetch_loan_data(args.loan_id)
        
        # 2. Create Domain Object
        snapshot = LoanSnapshot(
            application=raw_data["application"],
            borrowers=raw_data["borrowers"],
            properties=raw_data["properties"],
            liabilities=raw_data["liabilities"]
        )
        
        # 3. Validate
        print("Validating loan data...")
        loan_validator.validate_loan(snapshot)
        
        # 4. Generate XML
        print("Generating MISMO XML...")
        xml_content = build_mismo_xml(snapshot)
        
        # 5. Save to Disk
        with open(output_path, "wb") as f:
            f.write(xml_content)
            
        print(f"Success! MISMO XML saved to {output_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
