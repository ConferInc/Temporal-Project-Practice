"""
Document Ingestion Engine — "The Eyes"

Converts raw PDFs into clean Markdown text using Docling's DocumentConverter.
The output Markdown becomes the context fed to the LangGraph agent (brain.py).

Falls back to pypdf if Docling fails, ensuring the pipeline never hard-crashes
on a bad document.
"""
import os
import logging

logger = logging.getLogger(__name__)


def parse_document(file_path: str) -> str:
    """
    Parse a PDF document and return its content as clean Markdown text.

    Uses Docling's DocumentConverter for high-fidelity PDF-to-Markdown conversion.
    Falls back to pypdf for basic text extraction if Docling fails.

    Args:
        file_path: Absolute or relative path to the PDF file.

    Returns:
        Markdown string of the document content.

    Raises:
        FileNotFoundError: If the file does not exist.
        RuntimeError: If both Docling and pypdf fail to parse the document.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Document not found: {file_path}")

    # Primary: Docling (high-fidelity structured extraction)
    try:
        from docling.document_converter import DocumentConverter

        logger.info(f"Parsing document with Docling: {file_path}")
        converter = DocumentConverter()
        result = converter.convert(file_path)
        markdown_text = result.document.export_to_markdown()

        if markdown_text and markdown_text.strip():
            logger.info(f"Docling extracted {len(markdown_text)} chars from {file_path}")
            return markdown_text

        logger.warning("Docling returned empty text, falling back to pypdf")
    except Exception as e:
        logger.warning(f"Docling failed for {file_path}: {e}. Falling back to pypdf.")

    # Fallback: pypdf (basic text extraction, already a project dependency)
    try:
        from pypdf import PdfReader

        logger.info(f"Parsing document with pypdf fallback: {file_path}")
        reader = PdfReader(file_path)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)

        full_text = "\n\n".join(pages)

        if full_text.strip():
            logger.info(f"pypdf extracted {len(full_text)} chars from {file_path}")
            return full_text

        raise RuntimeError("pypdf returned empty text")
    except Exception as e:
        raise RuntimeError(
            f"All parsers failed for {file_path}. "
            f"Last error: {e}. "
            f"The document may be scanned/image-only or corrupted."
        )
