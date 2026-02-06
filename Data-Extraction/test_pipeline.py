"""
Test Pipeline - Bank Statement Processing
Runs BS.pdf through the complete pipeline and shows output at each step
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Fix for Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import pipeline components
# Imports moved to main for faster startup feedback

# Default output dir
OUTPUT_DIR = project_root / "output" / "pipeline_test"

def print_step(step_number, title):
    """Print a formatted step header"""
    print("\n" + "="*80)
    print(f"STEP {step_number}: {title}")
    print("="*80 + "\n")

def save_output(filename, content, is_json=True):
    """Save output to file"""
    global OUTPUT_DIR
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    filepath = OUTPUT_DIR / filename
    
    if is_json:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
    else:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print(f"✅ Saved to: {filepath}")
    return filepath

def main():
    global OUTPUT_DIR
    
    # Input file
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = str(project_root / "Test_upload_files" / "PS.pdf")
        
    # Set dynamic output directory
    input_filename = Path(file_path).stem
    OUTPUT_DIR = project_root / "output" / f"pipeline_test_{input_filename}"
    
    print("🚀 BANK STATEMENT PROCESSING PIPELINE")
    print(f"📄 Input: {file_path}")
    print(f"📂 Output Directory: {OUTPUT_DIR}\n")

    print("Loading pipeline components...")
    from tools.classifier import classify_document
    from tools.dockling_tool import extract_with_dockling
    from tools.structure_extractor import extract_canonical_structure
    from tools.normalization import normalize_data
    from tools.mismo_mapper import generate_mismo_xml
    from utils.semantic_distiller import process_dockling_data
    print("✅ Components loaded.\n")
    
    # ========================================================================
    # STEP 1: CLASSIFICATION
    # ========================================================================
    print_step(1, "DOCUMENT CLASSIFICATION")
    
    classification = classify_document(file_path)
    print(json.dumps(classification, indent=2))
    save_output("01_classification.json", classification)
    
    # Extract document type as string (not enum)
    document_category = classification.get("document_category", "Unknown")
    
    # Map document category to canonical mapper expected format
    doc_type_mapping = {
        "Bank Statement": "BankStatement",
        "Pay Stub": "PayStub",
        "W-2 Form": "W2",
        "URLA (Form 1003)": "URLA",
        "Government ID": "GovernmentID",
        "Tax Return (1040)": "TaxReturn",
        "Sales Contract": "SalesContract"
    }
    
    document_type = doc_type_mapping.get(document_category, document_category.replace(" ", ""))
    
    print(f"\n📋 Document Category: {document_category}")
    print(f"📋 Mapped Type: {document_type}")
    
    # ========================================================================
    # STEP 2: RAW EXTRACTION (JSON)
    # ========================================================================
    print_step(2, "RAW EXTRACTION")
    
    print("Using Dockling (structure-aware parsing)...")
    extraction_result = extract_with_dockling(file_path)
    
    raw_json = extraction_result.get("json", {})
    
    print(f"\nJSON Output keys: {list(raw_json.keys())}")
    save_output("02_raw_extraction.json", raw_json)
    
    # SEMANTIC DISTILLATION (COMPRESSION)
    print("\nApplying Semantic Distillation...")
    distilled_json = process_dockling_data(raw_json)
    
    print(f"Distilled JSON keys: {list(distilled_json.keys())}")
    save_output("02_distilled_structure.json", distilled_json)
    
    # ========================================================================
    # STEP 3: AI CANONICAL MAPPING
    # ========================================================================
    print_step(3, "AI CANONICAL MAPPING")
    
    print(f"Loading Canonical Schema...")
    schema_path = project_root / "resources" / "canonical_schema" / "schema.json"
    with open(schema_path, 'r', encoding='utf-8') as f:
        canonical_schema = json.load(f)
        
    print(f"Mapping {document_type} to canonical schema using LLM (Input: Distilled JSON)...")
    
    try:
        canonical_output = extract_canonical_structure(
            doc_data=distilled_json,
            schema=canonical_schema,
            document_type=document_type
        )
        
        print(f"✅ Canonical Structure extracted successfully")
        print(f"\n📋 Canonical Output:")
        print(json.dumps(canonical_output, indent=2))
        
        save_output("04_canonical_output.json", canonical_output)
        
    except Exception as e:
        print(f"❌ Error during canonical mapping: {e}")
        return

    # ========================================================================
    # STEP 5: NORMALIZATION
    # ========================================================================
    print_step(5, "NORMALIZATION")
    
    print("Normalizing canonical data...")
    normalized_output = normalize_data(canonical_output)
    
    print(f"\n📋 Normalized Output:")
    print(json.dumps(normalized_output, indent=2))
    
    save_output("05_normalized_output.json", normalized_output)

    # ========================================================================
    # STEP 6: MISMO XML GENERATION
    # ========================================================================
    print_step(6, "MISMO XML GENERATION")
    
    print("Generating MISMO 3.6 XML...")
    mismo_output = generate_mismo_xml(normalized_output)
    
    xml_str = mismo_output["mismo_xml"]
    
    print(f"\n📋 MISMO 3.6 XML Output (first 500 chars):")
    print("-" * 50)
    print(xml_str[:500])
    print("-" * 50)
    
    save_output("06_intermediate_mismo.json", mismo_output["intermediate_json"])
    with open(OUTPUT_DIR / "06_final_mismo.xml", 'w', encoding='utf-8') as f:
        f.write(xml_str)
    print(f"✅ Saved to: {OUTPUT_DIR / '06_final_mismo.xml'}")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "="*80)
    print("✅ PIPELINE COMPLETE")
    print("="*80)
    
    print(f"\n📊 Summary:")
    print(f"  • Document Type: {document_type}")
    print(f"  • Extraction Method: JSON (Dockling)")
    print(f"  • Canonical Sections: {list(canonical_output.keys())}")
    print(f"  • MISMO XML Generated: Yes")
    
    print(f"\n📁 All outputs saved to: {OUTPUT_DIR}")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
