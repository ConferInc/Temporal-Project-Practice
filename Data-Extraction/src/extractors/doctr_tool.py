import os
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from src.utils.logging import logger

# Initialize model globally to avoid reloading
try:
    model_doctr = ocr_predictor(pretrained=True)
except Exception as e:
    logger.error(f"Failed to load Doctr model: {e}")
    model_doctr = None


def _extract_structured_text_with_tables(result) -> str:
    """
    Extract text from DocTR result with table structure preservation.
    
    This function traverses the DocTR document structure to:
    1. Detect table regions (blocks with grid-like layout)
    2. Preserve table formatting using spacing and separators
    3. Maintain reading order while preserving structure
    
    Args:
        result: DocTR OCR result object with hierarchical structure
        
    Returns:
        Text with table structures preserved for regex pattern matching
    """
    output_lines = []
    
    try:
        for page in result.pages:
            page_lines = []
            
            # Process each block (paragraph or table region)
            for block in page.blocks:
                block_lines = []
                
                # Collect all lines in this block
                for line in block.lines:
                    line_text = " ".join([word.value for word in line.words])
                    if line_text.strip():
                        block_lines.append(line_text.strip())
                
                # If block has multiple lines with consistent column structure, treat as table
                if len(block_lines) > 2:
                    # Check if this looks like a table (has consistent spacing patterns)
                    # Heuristic: If lines have similar lengths and multiple words, likely a table
                    avg_words = sum(len(line.split()) for line in block_lines) / len(block_lines)
                    
                    if avg_words >= 3:  # Tables typically have multiple columns
                        # This looks like a table - preserve structure with separators
                        page_lines.append("=" * 60)  # Table start marker
                        for line in block_lines:
                            # Preserve spacing for column alignment
                            page_lines.append(line)
                        page_lines.append("=" * 60)  # Table end marker
                    else:
                        # Regular text block
                        page_lines.extend(block_lines)
                else:
                    # Small block - treat as regular text
                    page_lines.extend(block_lines)
                
                # Add spacing between blocks
                if block_lines:
                    page_lines.append("")
            
            output_lines.extend(page_lines)
            output_lines.append("\n")  # Page break
    
    except Exception as e:
        logger.warning(f"Structured extraction failed, falling back to simple render: {e}")
        # Fallback to simple rendering
        return result.render()
    
    return "\n".join(output_lines)


def extract_with_doctr(file_path: str, max_pages: int = None, preserve_tables: bool = True) -> str:
    """
    Extract text from document using DocTR OCR.
    
    Args:
        file_path: Path to PDF or image file
        max_pages: Optional limit on number of pages to process
        preserve_tables: If True, uses table-aware extraction (default: True)
        
    Returns:
        Extracted text with table structures preserved when preserve_tables=True
    """
    if model_doctr is None:
        return "Error: Doctr model not loaded."
        
    try:
        logger.info(f"Starting Doctr extraction for {file_path} (table-aware: {preserve_tables})")
        if file_path.lower().endswith(".pdf"):
            doc = DocumentFile.from_pdf(file_path)
        else:
            doc = DocumentFile.from_images(file_path)
            
        # Limit pages if max_pages is specified
        if max_pages and len(doc) > max_pages:
            logger.info(f"Limiting extraction to first {max_pages} pages (total {len(doc)})")
            doc = doc[:max_pages]
            
        result = model_doctr(doc)
        
        # Use structured extraction to preserve tables
        if preserve_tables:
            output = _extract_structured_text_with_tables(result)
            logger.info(f"Extracted {len(output)} chars with table structure preservation")
        else:
            output = result.render()
            logger.info(f"Extracted {len(output)} chars (simple mode)")
        
        # Save outputs for debugging/reference
        out_dir = os.path.join(os.path.dirname(file_path), "doctr_output")
        os.makedirs(out_dir, exist_ok=True)
        
        # Save structured output
        with open(os.path.join(out_dir, "output_structured.txt"), "w", encoding="utf-8") as f:
            f.write(output)
        
        # Also save simple render for comparison
        simple_output = result.render()
        with open(os.path.join(out_dir, "output_simple.txt"), "w", encoding="utf-8") as f:
            f.write(simple_output)
        
        logger.info(f"Structured: {len(output)} chars, Simple: {len(simple_output)} chars")
            
        return output
    except Exception as e:
        logger.error(f"Doctr extraction failed: {e}")
        return f"Error during Doctr extraction: {str(e)}"
