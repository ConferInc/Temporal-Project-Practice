"""
Test LLM Extraction Only
Uses existing markdown to verify LiteLLM connectivity and parsing.
"""
import os
import json
import traceback
from tools.structure_extractor import extract_structure
from dotenv import load_dotenv

load_dotenv()

def main():
    # Path to the temp markdown created by previous pipeline run
    md_path = "output/pipeline_test/temp_extraction.md"
    
    if not os.path.exists(md_path):
        print(f"❌ Markdown file not found: {md_path}")
        print("Please run the full pipeline once to generate OCR output first.")
        return

    print("🚀 Testing LLM Structure Extraction (LiteLLM)")
    print(f"Input: {md_path}")
    print(f"Base URL: {os.getenv('OPENAI_BASE_URL')}")
    print(f"Model: gpt-5.1") # As defined in logic
    
    try:
        # Extract as URLA
        output_json = extract_structure(md_path, document_type="URLA")
        
        print(f"\n✅ Extraction Success!")
        print(f"Saved to: {output_json}")
        
        # Read result
        with open(output_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        fields = data.get("extractedFields", {})
        print(f"\nExtracted {len(fields)} fields.")
        
        # Show sample
        print("Sample fields (first 5):")
        keys = list(fields.keys())[:5]
        for k in keys:
            print(f"  {k}: '{fields[k]}'")
            
    except Exception as e:
        print(f"\n❌ LLM Extraction Failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
