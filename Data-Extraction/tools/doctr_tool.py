import os
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from utils.logging import logger

# Initialize model globally to avoid reloading
try:
    model_doctr = ocr_predictor(pretrained=True)
except Exception as e:
    logger.error(f"Failed to load Doctr model: {e}")
    model_doctr = None

def extract_with_doctr(file_path: str, max_pages: int = None) -> str:
    if model_doctr is None:
        return "Error: Doctr model not loaded."
        
    try:
        logger.info(f"Starting Doctr extraction for {file_path}")
        if file_path.lower().endswith(".pdf"):
            doc = DocumentFile.from_pdf(file_path)
        else:
            doc = DocumentFile.from_images(file_path)
            
        # Limit pages if max_pages is specified
        if max_pages and len(doc) > max_pages:
            logger.info(f"Limiting extraction to first {max_pages} pages (total {len(doc)})")
            doc = doc[:max_pages]
            
        result = model_doctr(doc)
        output = result.render()
        
        # Save output for debugging/reference
        out_dir = os.path.join(os.path.dirname(file_path), "doctr_output")
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "output.txt"), "w", encoding="utf-8") as f:
            f.write(output)
            
        return output
    except Exception as e:
        logger.error(f"Doctr extraction failed: {e}")
        return f"Error during Doctr extraction: {str(e)}"
