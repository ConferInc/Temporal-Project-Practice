import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from fastmcp import FastMCP
from orchestrator.pipeline_router import route_document
from tools.classifier import classify_document
from tools.query import query_document
from tools.dockling_tool import extract_with_dockling
from tools.canonical_mapper import map_to_canonical_model
from tools.structure_extractor import extract_structure
from tools.mismo_mapper import generate_mismo_xml
from utils.logging import logger
import json

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
        result = route_document(file_path)
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
def ask_document(file_path: str, question: str) -> str:
    """
    Ask a question about a document.
    """
    try:
        return query_document(file_path, question)
    except Exception as e:
        logger.error(f"Error querying document: {e}")
        return f"Error: {str(e)}"

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
def map_to_canonical_schema(document_type: str, extracted_fields: dict) -> dict:
    """
    Map extracted document fields to canonical schema using rule-based logic.
    
    This tool uses deterministic mapping rules (NO LLM) to convert extracted
    key-value pairs into the canonical MISMO-compatible schema format.
    
    Args:
        document_type: Type of document (e.g., BankStatement, PayStub, URLA, GovernmentID)
        extracted_fields: Dictionary of extracted key-value pairs from the document
    
    Returns:
        Partial canonical JSON with only relevant sections populated
        
    Example:
        document_type = "BankStatement"
        extracted_fields = {
            "bankName": "Bank of America",
            "endingBalance": 25000,
            "accountNumber": "****1234"
        }
        
        Result:
        {
            "financials": {
                "assets": [{
                    "institutionName": "Bank of America",
                    "currentBalance": 25000,
                    "accountNumberMasked": "****1234"
                }]
            }
        }
    """
    try:
        return map_to_canonical_model(document_type, extracted_fields)
    except Exception as e:
        logger.error(f"Error mapping to canonical schema: {e}")
        return {"error": str(e)}

@mcp.tool()
def extract_structure_from_markdown(markdown_file_path: str, document_type: str = "Unknown") -> dict:
    """
    Extract structured key-value pairs from a Markdown file using LLM.
    Saves the result as a JSON file in the same directory.
    
    Args:
        markdown_file_path: Path to the Markdown file (e.g., output from Dockling)
        document_type: Type of document (e.g., URLA, BankStatement, PayStub, etc.)
    
    Returns:
        Dictionary with the path to the saved JSON file
    """
    try:
        output_path = extract_structure(markdown_file_path, document_type)
        return {
            "success": True,
            "output_file": output_path,
            "message": f"Successfully extracted structure and saved to {output_path}"
        }
    except Exception as e:
        logger.error(f"Error extracting structure: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def generate_mismo_xml_tool(canonical_data: dict) -> dict:
    """
    Convert Canonical JSON to MISMO v3.4 XML using deterministic mapping tables.
    
    Args:
        canonical_data: The v3 canonical JSON output.
        
    Returns:
        Dictionary containing:
        - intermediate_json: MISMO-structured JSON
        - mismo_xml: The final XML string
    """
    try:
        return generate_mismo_xml(canonical_data)
    except Exception as e:
        logger.error(f"Error generating MISMO XML: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    logger.info("Starting Utility MCP Server...")
    mcp.run()
