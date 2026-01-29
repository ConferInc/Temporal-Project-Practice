# Pyramid Architecture: Level 3 - The Workers (MCP Activities)
from .mcp_comms import CommsMCP, send_email, send_sms
from .mcp_encompass import EncompassMCP, create_loan_file, push_field_update

# Import original activities from the moved file
from .legacy import analyze_document, read_pdf_content, send_email_mock, organize_files

# Database Activities (Waiter Pattern Wiring)
from .db import (
    init_loan_record,
    update_loan_status,
    save_underwriting_decision,
    update_loan_ai_analysis,
    update_automated_underwriting,
    finalize_loan_record,
    get_loan_record,
)

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
    # Database Activities
    "init_loan_record",
    "update_loan_status",
    "save_underwriting_decision",
    "update_loan_ai_analysis",
    "update_automated_underwriting",
    "finalize_loan_record",
    "get_loan_record",
]