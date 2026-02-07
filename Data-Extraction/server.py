"""
FastMCP Server — Document Extraction API.

Exposes deterministic extraction tools over MCP protocol.
All tools use the src/ pipeline (zero LLM).
"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import json
import sys
from pathlib import Path

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).parent))

from fastmcp import FastMCP
from src.logic.classifier import classify_document
from src.logic.unified_extraction import unified_extract, unified_extract_multi
from src.extractors.dockling_tool import extract_with_dockling
from src.mapping.mismo_emitter import emit_mismo_xml
from src.preprocessing.converter import ensure_pdf, cleanup_temp
from src.preprocessing.splitter import split_document_blob, cleanup_chunks
from src.utils.logging import logger

# Initialize FastMCP Server
mcp = FastMCP("Utility Document Server")


@mcp.tool()
def process_document(file_path: str) -> dict:
    """
    Process a mortgage document through the unified pipeline.
    Classifies, extracts, maps, and normalizes the data.
    """
    try:
        logger.info(f"Received request to process: {file_path}")
        pdf_path = ensure_pdf(file_path)
        result = unified_extract(pdf_path, output_mode="flat")
        cleanup_temp()
        return result
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        return {"error": str(e)}


@mcp.tool()
def classify_file(file_path: str) -> dict:
    """
    Classify a document without full extraction.
    """
    try:
        return classify_document(file_path)
    except Exception as e:
        logger.error(f"Error classifying document: {e}")
        return {"error": str(e)}


@mcp.tool()
def parse_document_with_dockling(file_path: str) -> str:
    """
    Structure-aware parsing for digital, form-heavy PDFs using Dockling.
    Returns structured Markdown. Ideal for URLA-like forms.
    """
    try:
        return extract_with_dockling(file_path)
    except Exception as e:
        logger.error(f"Error parsing with Dockling: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
def generate_mismo_xml_tool(canonical_data: dict) -> dict:
    """
    Convert Canonical JSON to MISMO v3.4 XML using deterministic emitter.

    Args:
        canonical_data: The canonical JSON output from extraction.

    Returns:
        Dictionary containing the MISMO XML string.
    """
    try:
        xml_str = emit_mismo_xml(canonical_data)
        return {"mismo_xml": xml_str, "success": bool(xml_str)}
    except Exception as e:
        logger.error(f"Error generating MISMO XML: {e}")
        return {"error": str(e)}


@mcp.tool()
def process_mega_document(file_path: str) -> dict:
    """
    Process a mega-PDF: split into sub-documents, extract each chunk,
    and merge results into a single canonical model.
    """
    try:
        pdf_path = ensure_pdf(file_path)
        chunk_paths = split_document_blob(pdf_path)
        try:
            multi_result = unified_extract_multi(chunk_paths)
            return multi_result
        finally:
            cleanup_chunks(chunk_paths)
            cleanup_temp()
    except Exception as e:
        logger.error(f"Error processing mega document: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    logger.info("Starting Utility MCP Server...")
    mcp.run()
