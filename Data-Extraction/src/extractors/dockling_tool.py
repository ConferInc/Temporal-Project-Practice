import os
import json
from docling.document_converter import DocumentConverter, PdfFormatOption, InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableStructureOptions,
    TableFormerMode,
)
from src.utils.logging import logger


def _extract_table_as_text(table_data: dict) -> str:
    """
    Convert a Dockling table data structure into formatted text.
    
    Args:
        table_data: Dictionary with 'table_cells', 'num_rows', 'num_cols', 'grid'
        
    Returns:
        Formatted text representation of the table
    """
    try:
        cells = table_data.get("table_cells", [])
        num_rows = table_data.get("num_rows", 0)
        num_cols = table_data.get("num_cols", 0)
        
        if not cells or num_rows == 0 or num_cols == 0:
            return ""
        
        # Build grid
        grid = [[[] for _ in range(num_cols)] for _ in range(num_rows)]
        
        for cell in cells:
            text = cell.get("text", "").strip()
            if not text:
                continue
                
            start_row = cell.get("start_row_offset_idx", 0)
            end_row = cell.get("end_row_offset_idx", start_row + 1)
            start_col = cell.get("start_col_offset_idx", 0)
            end_col = cell.get("end_col_offset_idx", start_col + 1)
            
            # Place text in all spanned cells
            for r in range(start_row, min(end_row, num_rows)):
                for c in range(start_col, min(end_col, num_cols)):
                    if r < num_rows and c < num_cols:
                        grid[r][c].append(text)
        
        # Convert grid to text
        lines = []
        for row in grid:
            row_texts = []
            for cell in row:
                cell_text = " ".join(cell) if cell else ""
                row_texts.append(cell_text)
            
            # Join cells with separator
            line = " | ".join(row_texts)
            if line.strip():
                lines.append(line)
        
        return "\n".join(lines)
    
    except Exception as e:
        logger.warning(f"Failed to extract table as text: {e}")
        return ""


def _build_enriched_text(doc_dict: dict, markdown_text: str) -> str:
    """
    Build enriched text output that includes table data extracted from JSON.
    
    This function augments the markdown export with properly formatted table content
    that was lost in the markdown conversion.
    
    Args:
        doc_dict: Full document dictionary from Dockling
        markdown_text: Original markdown export
        
    Returns:
        Enhanced text with table content included
    """
    output_lines = []
    output_lines.append(markdown_text)
    output_lines.append("\n\n" + "=" * 80)
    output_lines.append("EXTRACTED TABLES (Table-Aware OCR)")
    output_lines.append("=" * 80 + "\n")
    
    tables = doc_dict.get("tables", [])
    
    for idx, table in enumerate(tables):
        table_data = table.get("data", {})
        
        if not table_data:
            continue
        
        # Get page number
        prov = table.get("prov", [])
        page_no = prov[0].get("page_no", "?") if prov else "?"
        
        output_lines.append(f"\n--- Table {idx + 1} (Page {page_no}) ---")
        
        # Get caption if available
        captions = table.get("captions", [])
        if captions:
            caption_texts = []
            for cap in captions:
                if isinstance(cap, dict) and "text" in cap:
                    caption_texts.append(cap["text"])
                elif isinstance(cap, str):
                    caption_texts.append(cap)
            if caption_texts:
                output_lines.append(f"Caption: {' '.join(caption_texts)}")
        
        # Extract and format table
        table_text = _extract_table_as_text(table_data)
        if table_text:
            output_lines.append(table_text)
        
        output_lines.append("")  # Blank line between tables
    
    return "\n".join(output_lines)


def extract_with_dockling(file_path: str) -> dict:
    """
    Extract document content using Docling with Markdown-first output.

    Returns:
        dict with keys:
            - "markdown": Clean markdown string (primary payload for LLM)
            - "meta": Metadata dict (page count, source file, etc.)
    """
    try:
        logger.info(f"Starting Dockling extraction for {file_path}")

        # Configure pipeline: tables ON, images OFF
        pdf_options = PdfPipelineOptions(
            do_table_structure=True,
            table_structure_options=TableStructureOptions(
                mode=TableFormerMode.ACCURATE,
                do_cell_matching=True,
            ),
            generate_page_images=False,
            generate_picture_images=False,
            do_ocr=True,
        )

        format_options = {
            InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_options),
        }

        converter = DocumentConverter(format_options=format_options)
        result = converter.convert(file_path)

        # Get document dict for table extraction
        doc_dict = result.document.export_to_dict()
        
        # Get markdown as base text
        markdown_text = result.document.export_to_markdown()
        
        # Build enriched text with table content
        enriched_text = _build_enriched_text(doc_dict, markdown_text)

        # Build lightweight metadata
        meta = {
            "source_file": os.path.basename(file_path),
            "num_pages": getattr(result.document, "num_pages", None),
            "markdown_length": len(markdown_text),
            "enriched_length": len(enriched_text),
            "tables_extracted": len(doc_dict.get("tables", [])),
        }

        # --- Debug artefacts (disk only, never returned upstream) ---
        out_dir = os.path.join(os.path.dirname(file_path), "dockling_output")
        os.makedirs(out_dir, exist_ok=True)

        # Save original markdown
        with open(os.path.join(out_dir, "output.md"), "w", encoding="utf-8") as f:
            f.write(markdown_text)
        
        # Save enriched text with tables
        with open(os.path.join(out_dir, "output_enriched.txt"), "w", encoding="utf-8") as f:
            f.write(enriched_text)

        # Save raw JSON for debugging only
        try:
            debug_json_path = os.path.join(out_dir, "debug.json")
            with open(debug_json_path, "w", encoding="utf-8") as f:
                json.dump(doc_dict, f, indent=2, ensure_ascii=False)
            logger.info(f"Debug JSON saved to {debug_json_path}")
        except Exception as debug_err:
            logger.warning(f"Could not save debug JSON: {debug_err}")

        logger.info(
            f"Dockling extraction complete: {meta['enriched_length']} chars "
            f"({meta['tables_extracted']} tables)"
        )
        
        # Return enriched text instead of plain markdown
        return {"markdown": enriched_text, "meta": meta}

    except Exception as e:
        logger.error(f"Dockling extraction failed: {e}")
        return {"error": f"Error during Dockling extraction: {str(e)}"}
