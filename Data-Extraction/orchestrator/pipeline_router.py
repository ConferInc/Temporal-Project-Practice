from tools.unified_extraction import unified_extract
from utils.logging import logger

def route_document(file_path: str):
    logger.info(f"Routing document: {file_path}")
    return unified_extract(file_path)
