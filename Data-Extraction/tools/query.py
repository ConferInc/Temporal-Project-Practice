from tools.doctr_tool import extract_with_doctr
from utils.logging import logger

def query_document(file_path: str, question: str) -> str:
    logger.info(f"Querying document {file_path} with question: {question}")
    # PRD Requirement: "Uses only docTR-extracted text", "No external knowledge"
    
    text = extract_with_doctr(file_path)
    
    # Simple lookup for now since we don't have an embedded LLM/Rag in this script without heavier deps like LangChain + Local LLM.
    # The prompt implies I am the AI agent who might use this tool, or this tool is for the USER to use via MCP.
    # If acts as a tool, it should probably return the text so the calling LLM can answer.
    # But PRD says "query_tool... Allow users to ask questions".
    # Implementation: Return the text relevant chunks or just full text if small?
    # Let's return the full text for the LLM to process since we are in an MCP context (Model Context Protocol).
    # The "Tool" provides context.
    
    return f"Document Content:\n{text}\n\n(Note: The answer to '{question}' should be derived from the above text.)"
