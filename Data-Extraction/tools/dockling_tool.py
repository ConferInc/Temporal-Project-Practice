import os
from docling.document_converter import DocumentConverter
from utils.logging import logger

def extract_with_dockling(file_path: str) -> dict:
    try:
        logger.info(f"Starting Dockling extraction for {file_path}")
        converter = DocumentConverter()
        result = converter.convert(file_path)
        markdown_text = result.document.export_to_markdown()
        json_data = result.document.export_to_dict()
        
        # Save output
        out_dir = os.path.join(os.path.dirname(file_path), "dockling_output")
        os.makedirs(out_dir, exist_ok=True)
        
        with open(os.path.join(out_dir, "output.md"), "w", encoding="utf-8") as f:
            f.write(markdown_text)
            
        with open(os.path.join(out_dir, "output.json"), "w", encoding="utf-8") as f:
            import json
            json.dump(json_data, f, indent=2, ensure_ascii=False)
            
        return {
            "markdown": markdown_text,
            "json": json_data
        }
    except Exception as e:
        logger.error(f"Dockling extraction failed: {e}")
        return {
            "error": f"Error during Dockling extraction: {str(e)}"
        }
