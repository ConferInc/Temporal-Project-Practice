"""
Image-to-PDF Converter — Preprocessing Layer.

Ensures every input entering the pipeline is a clean PDF.
Handles: PDF passthrough, JPG/PNG → PDF, HEIC → JPG → PDF.

Output goes to a ``temp/`` directory so originals are never modified.

Dependencies: Pillow (PIL), pillow-heif (optional, for HEIC).
"""

import os
import shutil
import tempfile
from pathlib import Path

from PIL import Image

# Supported image extensions (case-insensitive check at call site)
_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
_HEIC_EXTENSIONS = {".heic", ".heif"}
_PDF_EXTENSION = ".pdf"

# Module-level temp dir — cleaned up explicitly via cleanup_temp()
_TEMP_DIR: str | None = None


def _get_temp_dir() -> str:
    """Lazily create a per-session temp directory."""
    global _TEMP_DIR
    if _TEMP_DIR is None or not os.path.isdir(_TEMP_DIR):
        _TEMP_DIR = tempfile.mkdtemp(prefix="converter_")
    return _TEMP_DIR


def ensure_pdf(file_path: str) -> str:
    """Convert *file_path* to a PDF if necessary.

    Returns:
        Absolute path to a PDF file.  If the input is already a PDF the
        original path is returned unchanged.  Otherwise a new PDF is
        written into a temp directory and its path is returned.

    Raises:
        FileNotFoundError: if *file_path* does not exist.
        ValueError: if the file type is unsupported.
    """
    path = Path(file_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    ext = path.suffix.lower()

    # --- PDF passthrough ---
    if ext == _PDF_EXTENSION:
        return str(path)

    # --- HEIC → JPG → PDF ---
    if ext in _HEIC_EXTENSIONS:
        return _heic_to_pdf(path)

    # --- Standard image → PDF ---
    if ext in _IMAGE_EXTENSIONS:
        return _image_to_pdf(path)

    raise ValueError(
        f"Unsupported file type '{ext}'. "
        f"Accepted: .pdf, {', '.join(sorted(_IMAGE_EXTENSIONS | _HEIC_EXTENSIONS))}"
    )


# ---------------------------------------------------------------------------
# Private converters
# ---------------------------------------------------------------------------

def _image_to_pdf(image_path: Path) -> str:
    """Convert a standard image (JPG/PNG/BMP/TIFF) to a single-page PDF."""
    img = Image.open(image_path)

    # Convert RGBA/palette to RGB (PDF doesn't support alpha)
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")

    out_name = image_path.stem + ".pdf"
    out_path = os.path.join(_get_temp_dir(), out_name)

    img.save(out_path, "PDF", resolution=150)
    img.close()
    return out_path


def _heic_to_pdf(heic_path: Path) -> str:
    """Convert a HEIC/HEIF image to PDF (via intermediate JPG)."""
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
    except ImportError:
        raise ImportError(
            "pillow-heif is required for HEIC support. "
            "Install it with: pip install pillow-heif"
        )

    img = Image.open(heic_path)
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")

    out_name = heic_path.stem + ".pdf"
    out_path = os.path.join(_get_temp_dir(), out_name)

    img.save(out_path, "PDF", resolution=150)
    img.close()
    return out_path


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

def cleanup_temp() -> None:
    """Remove the converter temp directory and all its contents."""
    global _TEMP_DIR
    if _TEMP_DIR and os.path.isdir(_TEMP_DIR):
        shutil.rmtree(_TEMP_DIR, ignore_errors=True)
        _TEMP_DIR = None
