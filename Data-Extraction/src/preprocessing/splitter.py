"""
Document Splitter — "Anchor & Continuity" Algorithm.

Splits a multi-document (mega) PDF blob into individual typed chunks.

Algorithm:
    1. Iterate pages with ``pypdf``.
    2. Extract native text.  If sparse (< 50 chars), OCR the **top 30 %**
       of the page with ``RapidOCR``.
    3. Match header text against anchor signatures from
       ``src/rules/signatures.yaml``.
    4. *Match found*  → start new document group.
       *No match*     → append to current group (continuity).
    5. Write each group to ``temp/chunk_{i}_{type}.pdf``.

Dependencies: pypdf, PyYAML, RapidOCR (optional — graceful degradation).
"""

import logging
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from pypdf import PdfReader, PdfWriter

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Signature matching
# ---------------------------------------------------------------------------

_SIGNATURES: list | None = None
_SIG_PATH = os.path.join(os.path.dirname(__file__), "..", "rules", "signatures.yaml")


def _load_signatures() -> list:
    """Load and cache signatures from YAML."""
    global _SIGNATURES
    if _SIGNATURES is None:
        if not os.path.exists(_SIG_PATH):
            logger.error(f"[SPLITTER] signatures.yaml NOT FOUND at {_SIG_PATH}")
            _SIGNATURES = []
            return _SIGNATURES
        with open(_SIG_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        _SIGNATURES = data.get("signatures", [])
        logger.debug(f"[SPLITTER] Loaded {len(_SIGNATURES)} signatures from {_SIG_PATH}")
    return _SIGNATURES


def _keyword_in_text(keyword: str, text_lower: str) -> bool:
    """Check if a keyword matches text, resilient to OCR word-fusion.

    Multi-word keywords like "uniform residential loan application" are
    split into individual words; ALL words must be present in the text
    (but not necessarily contiguous).  This handles OCR output like
    "UniformResidentialLoanApplication" → "uniformresidentialloanapplication".
    """
    words = keyword.lower().split()
    if len(words) <= 1:
        # Single word — direct substring match
        return keyword.lower() in text_lower
    # Multi-word — every word must appear somewhere in the text
    return all(w in text_lower for w in words)


def _match_page(text: str) -> Tuple[Optional[str], float]:
    """Score *text* against all signatures.

    Returns:
        (doc_type, score) if matched, or (None, 0.0) if no match.
    """
    if not text or not text.strip():
        return None, 0.0

    text_lower = text.lower()
    sigs = _load_signatures()

    best_type: str | None = None
    best_score = 0.0

    for sig in sigs:
        doc_type = sig["doc_type"]
        minimum_score = sig.get("minimum_score", 0.3)

        # Required keywords — all must match
        required = sig.get("required_keywords") or []
        if required and not all(_keyword_in_text(kw, text_lower) for kw in required):
            continue

        # Keyword scoring (1 point each)
        keywords = sig.get("keywords") or []
        keyword_hits = sum(1 for kw in keywords if _keyword_in_text(kw, text_lower))

        # Regex scoring (2 points each)
        patterns = sig.get("regex_patterns") or []
        regex_hits = sum(
            1 for pat in patterns if re.search(pat, text, re.IGNORECASE)
        )

        total_possible = len(keywords) + len(patterns) * 2
        if total_possible == 0:
            continue

        score = (keyword_hits + regex_hits * 2) / total_possible
        if score >= minimum_score and score > best_score:
            best_score = score
            best_type = doc_type

    return best_type, best_score


# ---------------------------------------------------------------------------
# OCR helper (optional RapidOCR)
# ---------------------------------------------------------------------------

_rapidocr_engine = None


def _ocr_header(page_image_bytes: bytes) -> str:
    """OCR page-header image bytes using RapidOCR. Returns text or ''."""
    global _rapidocr_engine
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        logger.warning("[SPLITTER] RapidOCR not installed — OCR fallback disabled")
        return ""

    if _rapidocr_engine is None:
        _rapidocr_engine = RapidOCR()

    result, _ = _rapidocr_engine(page_image_bytes)
    if result is None:
        return ""
    return " ".join(line[1] for line in result)


def _render_page_header(pdf_path: str, page_index: int) -> bytes:
    """Render the top 30% of a page as a PNG image (uses PyMuPDF/fitz)."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.warning("[SPLITTER] PyMuPDF not installed — cannot render page headers for OCR")
        return b""

    doc = fitz.open(pdf_path)
    page = doc[page_index]
    rect = page.rect
    clip = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y0 + rect.height * 0.3)
    pix = page.get_pixmap(clip=clip, dpi=150)
    img_bytes = pix.tobytes("png")
    doc.close()
    return img_bytes


# ---------------------------------------------------------------------------
# Page text extraction (with OCR fallback + logging)
# ---------------------------------------------------------------------------

_MIN_TEXT_LENGTH = 50  # chars below which we try OCR fallback


def _extract_page_text(pdf_path: str, reader: PdfReader, page_idx: int) -> Tuple[str, str]:
    """Extract text from a single page with OCR fallback.

    Returns:
        (text, method) where method is 'pypdf', 'ocr', or 'empty'.
    """
    text = reader.pages[page_idx].extract_text() or ""
    method = "pypdf"

    if len(text.strip()) < _MIN_TEXT_LENGTH:
        # pypdf returned insufficient text — try OCR on header region
        header_bytes = _render_page_header(pdf_path, page_idx)
        if header_bytes:
            ocr_text = _ocr_header(header_bytes)
            if ocr_text:
                text = ocr_text
                method = "ocr"
            else:
                method = "ocr-empty"
        else:
            method = "no-renderer"

    return text, method


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def split_document_blob(file_path: str) -> List[str]:
    """Split a mega-PDF into per-document-type chunk PDFs.

    Args:
        file_path: path to the input PDF.

    Returns:
        List of paths to chunk PDFs written under a ``temp/`` directory.
        Caller is responsible for deleting these when done (or call
        ``cleanup_chunks(paths)``).
    """
    file_path = str(Path(file_path).resolve())
    reader = PdfReader(file_path)
    total_pages = len(reader.pages)

    print(f"  [SPLITTER] Document has {total_pages} pages. Scanning for anchors...")
    logger.info(f"[SPLITTER] Splitting {file_path} ({total_pages} pages)")

    # Each group: {"doc_type": str, "pages": [int, ...]}
    groups: List[Dict] = []
    current_group: Optional[Dict] = None

    for idx in range(total_pages):
        text, method = _extract_page_text(file_path, reader, idx)
        char_count = len(text.strip())

        # Log page content detection
        header_sample = text.strip()[:80].replace("\n", " ")
        logger.debug(
            f"[SPLITTER] Page {idx}: {char_count} chars via {method}. "
            f'Header: "{header_sample}..."'
        )
        print(
            f"    Page {idx + 1}/{total_pages}: {char_count:>5} chars "
            f"[{method:>10}] ", end=""
        )

        # Match against anchor signatures
        match_type, score = _match_page(text)

        if match_type is not None:
            print(f'-> ANCHOR: "{match_type}" (score={score:.0%})')
            logger.info(
                f"[SPLITTER] Page {idx}: ANCHOR '{match_type}' (score={score:.2f})"
            )
            current_group = {"doc_type": match_type, "pages": [idx]}
            groups.append(current_group)
        else:
            group_label = current_group["doc_type"] if current_group else "Unknown"
            print(f"   (continuation of {group_label})")
            logger.debug(f"[SPLITTER] Page {idx}: no match, continuation of {group_label}")

            if current_group is not None:
                current_group["pages"].append(idx)
            else:
                current_group = {"doc_type": "Unknown", "pages": [idx]}
                groups.append(current_group)

    # --- Write each group to a chunk PDF ---
    temp_dir = tempfile.mkdtemp(prefix="splitter_")
    chunk_paths: List[str] = []

    print(f"\n  [SPLITTER] Writing {len(groups)} chunk(s):")
    for i, group in enumerate(groups):
        safe_type = (
            group["doc_type"]
            .replace(" ", "")
            .replace("(", "")
            .replace(")", "")
        )
        filename = f"chunk_{i:03d}_{safe_type}.pdf"
        out_path = os.path.join(temp_dir, filename)

        writer = PdfWriter()
        for page_idx in group["pages"]:
            writer.add_page(reader.pages[page_idx])
        with open(out_path, "wb") as f:
            writer.write(f)

        page_range = f"{group['pages'][0]+1}-{group['pages'][-1]+1}"
        print(f"    Chunk {i}: {group['doc_type']:30s} pages {page_range:>6s} -> {filename}")
        logger.info(
            f"[SPLITTER] Chunk {i}: {group['doc_type']} "
            f"pages {page_range} -> {out_path}"
        )
        chunk_paths.append(out_path)

    return chunk_paths


def is_mega_pdf(file_path: str) -> bool:
    """Quick heuristic: sample pages for > 1 doc type.

    Samples up to 5 evenly-spaced pages (first, 25%, 50%, 75%, last).
    Uses OCR fallback for scanned pages. Resilient to OCR word-fusion.
    """
    reader = PdfReader(file_path)
    total = len(reader.pages)

    if total <= 1:
        logger.debug(f"[SPLITTER] is_mega_pdf: {total} page(s), returning False")
        return False

    # Sample up to 5 evenly-spaced pages for better coverage
    if total <= 5:
        sample_indices = list(range(total))
    else:
        sample_indices = list({0, total // 4, total // 2, 3 * total // 4, total - 1})
    sample_indices.sort()

    detected_types = set()
    file_path_str = str(Path(file_path).resolve())

    for idx in sample_indices:
        text, method = _extract_page_text(file_path_str, reader, idx)
        match_type, score = _match_page(text)
        if match_type:
            detected_types.add(match_type)
            logger.debug(
                f"[SPLITTER] is_mega_pdf: page {idx} -> {match_type} "
                f"(score={score:.2f}, method={method})"
            )

    is_mega = len(detected_types) > 1
    logger.info(
        f"[SPLITTER] is_mega_pdf: {total} pages, sampled {len(sample_indices)}, "
        f"found {len(detected_types)} type(s): {detected_types} -> {is_mega}"
    )
    return is_mega


def cleanup_chunks(chunk_paths: List[str]) -> None:
    """Delete chunk files and their parent temp directory."""
    if not chunk_paths:
        return
    temp_dir = os.path.dirname(chunk_paths[0])
    if temp_dir and os.path.isdir(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)
