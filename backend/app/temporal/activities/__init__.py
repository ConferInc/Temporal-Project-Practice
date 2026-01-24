# Pyramid Architecture: Level 3 - The Workers (MCP Activities)
from .mcp_comms import CommsMCP, send_email, send_sms
from .mcp_encompass import EncompassMCP, create_loan_file, push_field_update

# Import original activities from the moved file
from .legacy import analyze_document, read_pdf_content, send_email_mock, organize_files

__all__ = [
    # New MCPs
    "CommsMCP",
    "EncompassMCP",
    "send_email",
    "send_sms",
    "create_loan_file",
    "push_field_update",
    # Legacy Activities
    "analyze_document",
    "read_pdf_content",
    "send_email_mock",
    "organize_files",
]