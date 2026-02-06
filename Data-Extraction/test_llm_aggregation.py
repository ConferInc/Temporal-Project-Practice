import json
import os
import sys
from typing import Dict

# Ensure we can import from tools
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.canonical_mapper import map_to_canonical_model, get_mapper
from utils.logging import logger

def test_aggregation():
    logger.info("🧪 Starting LLM Aggregation Test")
    
    # Mock Data 1: URLA (Borrower Info)
    urla_extracted = {
        "borrowerName": "John Doe",
        "borrowerSSN": "123-45-6789",
        "loanAmount": 350000,
        "propertyAddress": "123 Main St"
    }
    
    logger.info("1️⃣ Processing URLA (Base)...")
    canonical_1 = map_to_canonical_model("URLA", urla_extracted)
    
    print("\n--- Canonical 1 (URLA) ---")
    print(json.dumps(canonical_1.get("deal", {}).get("parties", []), indent=2))
    
    # Mock Data 2: Bank Statement (Asset Info)
    # Should be merged into the SAME "deal" but potentially add assets
    bs_extracted = {
        "accountNumber": "88889999",
        "bankName": "Chase Bank",
        "endingBalance": 15000,
        "statementDate": "2023-10-01"
    }
    
    logger.info("2️⃣ Processing Bank Statement (Aggregating)...")
    # PASS existing canonical_1 to merge
    canonical_2 = map_to_canonical_model("BankStatement", bs_extracted, existing_canonical=canonical_1)
    
    print("\n--- Canonical 2 (Aggregated) ---")
    # Check if we have both Borrower (from URLA) and Assets (from BS)
    deal = canonical_2.get("deal", {})
    parties = deal.get("parties", [])
    assets = deal.get("assets", [])
    
    print(f"Parties Count: {len(parties)}")
    print(f"Assets Count: {len(assets)}")
    
    if len(parties) >= 1 and len(assets) >= 1:
        print("✅ SUCCESS: Aggregation merged Parties and Assets!")
    else:
        print("❌ FAILURE: Data missing or overwritten.")
        
    print(json.dumps(deal, indent=2))

if __name__ == "__main__":
    test_aggregation()
