import logging
import sys
import os

def setup_logging(log_file="logs/server.log"):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logger = logging.getLogger("utility_mcp")
    logger.setLevel(logging.INFO)
    
    # CRITICAL: Disable propagation to root logger to prevent stdout pollution
    logger.propagate = False
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # File Handler ONLY (no console output to avoid MCP stdio pollution)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()
