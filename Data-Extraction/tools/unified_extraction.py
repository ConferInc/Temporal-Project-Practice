import os
import json
from typing import Dict, Any, Optional
from tools.classifier import classify_document
from tools.doctr_tool import extract_with_doctr
from tools.dockling_tool import extract_with_dockling
from tools.dockling_tool import extract_with_dockling
from tools.structure_extractor import extract_canonical_structure
from tools.normalization import normalize_data
from utils.schema_registry import get_schema_registry
from utils.semantic_distiller import process_dockling_data
from utils.logging import logger

def unified_extract(file_path: str, existing_canonical: Optional[Dict] = None):
    logger.info(f"Starting unified extraction for {file_path}")
    
    # 1. Classify
    decision = classify_document(file_path)
    extractor = decision.get("recommended_tool")
    document_type = decision.get("document_category")
    
    # 2. Extract raw text/markdown
    raw_data = ""
    # Map recommended_tool strings to extractors
    if extractor == "parse_document_with_dockling":
        raw_data = extract_with_dockling(file_path)
        extraction_type = "markdown"
    elif extractor == "ocr_document":
        raw_data = extract_with_doctr(file_path)
        extraction_type = "text"
    else:
        # Fallback
        logger.warning(f"Unknown extractor '{extractor}', defaulting to Doctr")
        raw_data = extract_with_doctr(file_path)
        extraction_type = "text"
    
    # 3. Structure Extraction & Canonical Mapping
    logger.info("Extracting structured fields using LLM...")
    
    # Save raw extraction to temp file for debugging
    temp_dir = os.path.join(os.path.dirname(file_path), "temp_extraction")
    os.makedirs(temp_dir, exist_ok=True)
    temp_md_path = os.path.join(temp_dir, "temp_extraction.md")
    
    with open(temp_md_path, 'w', encoding='utf-8') as f:
        f.write(raw_data)
        
    extracted_fields = {}
    canonical_data = {}
    
    try:
        # Prepare Schema
        if "URLA" in document_type or "1003" in document_type:
            logger.info("Detected URLA document - Loading dedicated URLA Schema")
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            urla_schema_path = os.path.join(base_path, "schema", "urla.json")
            with open(urla_schema_path, 'r', encoding='utf-8') as f:
                target_schema = json.load(f)
        else:
             logger.info(f"Using Standard Canonical Schema for {document_type}")
             target_schema = get_schema_registry().get_schema()

        # Prepare Data (Semantic Distillation)
        # Note: extract_canonical_structure expects a dict. 
        # If raw_data is a string (Markdown/OCR), we might need to wrap it or use it as is?
        # extract_with_dockling returns full dict. extract_with_doctr returns string.
        # Check extraction_type.
        
        doc_data_input = {}
        if extraction_type == "markdown":
            # Re-read raw data if it was returned as dict? 
            # extract_with_dockling returns a dict with 'json', 'markdown'.
            # unified_extract extraction calls:
            # raw_data = extract_with_dockling(file_path) -> returns DICT usually?
            # Let's check extract_with_dockling return type in code... 
            # Step 12 says: return extract_with_dockling(file_path) -> returns str (docstring says "Returns structured Markdown")
            # Step 18 says: raw_data = extract_with_dockling(file_path)
            # But test_pipeline.py Step 2 says: extraction_result = extract_with_dockling(file_path); raw_json = extraction_result.get("json", {})
            # This implies extract_with_dockling returns a DICT.
            # unified_extraction line 24 assigns it to raw_data.
            pass
        
        # We need to handle the data format for extract_canonical_structure
        # It expects "doc_data: dict".
        
        if isinstance(raw_data, dict) and "json" in raw_data:
             distilled_data = process_dockling_data(raw_data["json"])
             doc_data_input = distilled_data
        elif isinstance(raw_data, str):
             # For OCR text, wrap it
             doc_data_input = {"text_content": raw_data}
        else:
             doc_data_input = raw_data if isinstance(raw_data, dict) else {"content": str(raw_data)}

        # Extract using LLM directly to Canonical/URLA Schema
        canonical_data = extract_canonical_structure(
            doc_data=doc_data_input,
            schema=target_schema,
            document_type=document_type
        )
        
        extracted_fields = canonical_data # For this flow, they are the same
        logger.info(f"✅ Extracted canonical structure for {document_type}")
        
    except Exception as e:
        logger.error(f"Structure extraction failed: {e}")
        canonical_data = {}
        
    # 4. Canonical Mapping - SKIPPED (Merged into Step 3)
    # The extraction above already produced the target schema structure.

    
    # 5. Normalization
    normalized_data = normalize_data(canonical_data)
    
    result = {
        "classification": decision,
        "raw_extraction_summary": raw_data[:500] + "...",  # Summary to avoid huge output
        "extracted_fields": extracted_fields,
        "canonical_data": canonical_data,
        "normalized_data": normalized_data
    }
    
    return result
