import os
import json
from typing import Dict, Any, List, Optional
from src.logic.classifier import classify_document
from src.extractors.doctr_tool import extract_with_doctr
from src.extractors.dockling_tool import extract_with_dockling
from src.mapping.rule_engine import extract_with_rules
from src.mapping.canonical_assembler import CanonicalAssembler
from src.processing.normalization import normalize_data
from src.utils.logging import logger


def unified_extract(
    file_path: str,
    existing_canonical: Optional[Dict] = None,
    output_mode: str = "nested",
):
    """Process a single document through the extraction pipeline.

    Args:
        file_path: path to input PDF/image
        existing_canonical: unused (kept for backward compat)
        output_mode: "nested" (default, backward-compatible) or "flat"
                     When "flat", uses two-stage extraction:
                     RuleEngine(flat) → CanonicalAssembler → deep dict
    """
    logger.info(f"Starting unified extraction for {file_path}")

    # 1. Classify
    decision = classify_document(file_path)
    extractor = decision.get("recommended_tool")
    document_type = decision.get("document_category")

    # 2. Extract raw content  (always prefer Docling for markdown)
    if extractor == "parse_document_with_dockling":
        raw_data = extract_with_dockling(file_path)
        extraction_type = "markdown"
    elif extractor == "ocr_document":
        raw_data = extract_with_doctr(file_path)
        extraction_type = "text"
    else:
        logger.warning(f"Unknown extractor '{extractor}', defaulting to Doctr")
        raw_data = extract_with_doctr(file_path)
        extraction_type = "text"

    # 3. Deterministic Structure Extraction  (Rule Engine — zero LLM)
    logger.info("Extracting structured fields using Rule Engine (deterministic)...")

    extracted_fields = {}
    canonical_data = {}

    try:
        # Get the markdown content for the rule engine
        if extraction_type == "markdown":
            if isinstance(raw_data, dict) and "error" not in raw_data:
                markdown_content = raw_data.get("markdown", "")
            else:
                error_msg = (
                    raw_data.get("error", "Unknown extraction error")
                    if isinstance(raw_data, dict) else str(raw_data)
                )
                logger.error(f"Dockling extraction returned error: {error_msg}")
                markdown_content = ""
        else:
            # OCR text is plain text — rule engine handles it the same way
            markdown_content = raw_data if isinstance(raw_data, str) else str(raw_data)

        if output_mode == "flat":
            # Two-stage: flat extraction → canonical assembly
            flat_data = extract_with_rules(
                markdown=markdown_content,
                document_type=document_type,
                output_mode="flat",
            )
            assembler = CanonicalAssembler()
            canonical_data = assembler.assemble(flat_data, document_type)
            extracted_fields = flat_data
        else:
            # Legacy: direct nested extraction
            canonical_data = extract_with_rules(
                markdown=markdown_content,
                document_type=document_type,
            )
            extracted_fields = canonical_data

        logger.info(f"Extracted canonical structure for {document_type}")

    except Exception as e:
        logger.error(f"Structure extraction failed: {e}")
        canonical_data = {}

    # 4. Normalization
    normalized_data = normalize_data(canonical_data)

    # Build summary for raw_extraction (avoid dumping entire content)
    if isinstance(raw_data, dict):
        raw_summary = raw_data.get("markdown", "")[:500] + "..."
    elif isinstance(raw_data, str):
        raw_summary = raw_data[:500] + "..."
    else:
        raw_summary = str(raw_data)[:500] + "..."

    result = {
        "classification": decision,
        "raw_extraction_summary": raw_summary,
        "extracted_fields": extracted_fields,
        "canonical_data": canonical_data,
        "normalized_data": normalized_data,
    }

    return result


def unified_extract_multi(file_paths: List[str]) -> dict:
    """Process multiple documents, merge, and assemble into single canonical.

    Uses the two-stage flat extraction pipeline:
    1. Extract each document in flat mode
    2. Merge all flat dicts (priority-based conflict resolution)
    3. Assemble merged flat dict into deep canonical JSON

    Args:
        file_paths: list of paths to input PDFs/images

    Returns:
        Deep canonical JSON dict with merged data from all documents
    """
    from src.logic.merger import DocumentMerger

    merger = DocumentMerger()
    assembler = CanonicalAssembler()

    extractions = []
    all_classifications = []

    for path in file_paths:
        result = unified_extract(path, output_mode="flat")
        doc_type = result["classification"]["document_category"]
        flat_data = result["extracted_fields"]
        extractions.append((doc_type, flat_data))
        all_classifications.append(result["classification"])

    # Merge all flat dicts
    merged_flat = merger.merge(extractions)

    # Party matching (informational — logged for debugging)
    party_map = merger.match_parties(extractions)
    logger.info(f"Party identity map: {party_map}")

    # Assemble into deep canonical
    canonical = assembler.assemble(merged_flat, "merged")

    return {
        "classifications": all_classifications,
        "merged_flat": merged_flat,
        "canonical_data": canonical,
        "party_map": party_map,
    }
