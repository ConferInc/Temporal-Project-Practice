import os
import json
from docling.document_converter import DocumentConverter, PdfFormatOption, InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableStructureOptions,
    TableFormerMode,
)
from src.utils.logging import logger


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

        markdown_text = result.document.export_to_markdown()

        # Build lightweight metadata
        meta = {
            "source_file": os.path.basename(file_path),
            "num_pages": getattr(result.document, "num_pages", None),
            "markdown_length": len(markdown_text),
        }

        # --- Debug artefacts (disk only, never returned upstream) ---
        out_dir = os.path.join(os.path.dirname(file_path), "dockling_output")
        os.makedirs(out_dir, exist_ok=True)

        with open(os.path.join(out_dir, "output.md"), "w", encoding="utf-8") as f:
            f.write(markdown_text)

        # Save raw JSON for debugging only
        try:
            json_data = result.document.export_to_dict()
            debug_json_path = os.path.join(out_dir, "debug.json")
            with open(debug_json_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Debug JSON saved to {debug_json_path}")
        except Exception as debug_err:
            logger.warning(f"Could not save debug JSON: {debug_err}")

        logger.info(
            f"Dockling extraction complete: {meta['markdown_length']} chars of markdown"
        )
        return {"markdown": markdown_text, "meta": meta}

    except Exception as e:
        logger.error(f"Dockling extraction failed: {e}")
        return {"error": f"Error during Dockling extraction: {str(e)}"}
