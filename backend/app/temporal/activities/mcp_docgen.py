"""
Pyramid Architecture: Level 3 - Document Generation MCP Worker

The DocGenMCP handles automated document generation:
- Initial Disclosures
- Loan Estimates
- Other templated documents

Uses fpdf2 for PDF generation.
"""
import os
from dataclasses import dataclass
from temporalio import activity
from datetime import datetime
from fpdf import FPDF


# Document Templates (Knowledge Base)
TEMPLATES = {
    "Initial Disclosures": """
INITIAL DISCLOSURES

Date: {date}

Borrower: {name}
Email: {email}

LOAN SUMMARY
---------------------------------------------------------
Property Value:      ${property_value:,.2f}
Down Payment:        ${down_payment:,.2f}
Loan Amount:         ${loan_amount:,.2f}
Interest Rate:       {rate}% Fixed
Loan Term:           {term} years
Estimated Monthly Payment: ${monthly_payment:,.2f}

IMPORTANT DISCLOSURES
---------------------------------------------------------
This is not a commitment to lend. Your actual rate, payment,
and costs may vary based on your specific situation.

Equal Housing Lender. NMLS #12345

This disclosure is provided in compliance with federal
regulations and is intended to help you understand your
potential loan terms.

By proceeding with this application, you acknowledge
receipt of these initial disclosures.
""",
    "Loan Estimate": """
LOAN ESTIMATE

Prepared for: {name}
Date: {date}

LOAN TERMS
---------------------------------------------------------
Loan Amount:    ${loan_amount:,.2f}
Interest Rate:  {rate}%
Monthly P&I:    ${monthly_payment:,.2f}

This estimate is valid for 10 business days.
""",
}


def calculate_monthly_payment(loan_amount: float, rate: float = 6.5, term_years: int = 30) -> float:
    """
    Calculate monthly payment using standard amortization formula.

    Args:
        loan_amount: Principal loan amount
        rate: Annual interest rate (default 6.5%)
        term_years: Loan term in years (default 30)

    Returns:
        Monthly payment amount
    """
    if loan_amount <= 0:
        return 0.0

    monthly_rate = (rate / 100) / 12
    num_payments = term_years * 12

    if monthly_rate == 0:
        return loan_amount / num_payments

    payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / \
              ((1 + monthly_rate) ** num_payments - 1)

    return round(payment, 2)


@dataclass
class DocGenMCP:
    """Document Generation MCP - handles PDF creation"""

    @staticmethod
    def generate_document(doc_type: str, data: dict, config: dict = None) -> dict:
        """
        Generate a PDF document from a template.

        Args:
            doc_type: Document type (e.g., "Initial Disclosures", "Loan Estimate")
            data: Data dictionary for template rendering
            config: Optional config (e.g., custom paths)

        Returns:
            Dict with file_path and public_url
        """
        config = config or {}

        # Get template
        template = TEMPLATES.get(doc_type)
        if not template:
            raise ValueError(f"Unknown document type: {doc_type}")

        # Extract data with defaults
        workflow_id = data.get("workflow_id", "unknown")
        name = data.get("name", "Unknown Borrower")
        email = data.get("email", "N/A")
        property_value = float(data.get("property_value", 0))
        down_payment = float(data.get("down_payment", 0))
        loan_amount = float(data.get("loan_amount", property_value - down_payment))
        rate = float(data.get("rate", 6.5))
        term = int(data.get("term", 30))

        # Calculate monthly payment if not provided
        monthly_payment = data.get("monthly_payment")
        if monthly_payment is None:
            monthly_payment = calculate_monthly_payment(loan_amount, rate, term)
        else:
            monthly_payment = float(monthly_payment)

        # Format date
        date_str = datetime.utcnow().strftime("%B %d, %Y")

        # Render template
        rendered_text = template.format(
            date=date_str,
            name=name,
            email=email,
            property_value=property_value,
            down_payment=down_payment,
            loan_amount=loan_amount,
            rate=rate,
            term=term,
            monthly_payment=monthly_payment
        )

        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Courier", size=10)

        # Add content line by line
        for line in rendered_text.strip().split("\n"):
            pdf.cell(0, 5, line, ln=True)

        # Determine output path
        base_dir = os.path.dirname(os.path.abspath(__file__))
        uploads_root = os.path.join(base_dir, "..", "..", "..", "uploads")
        app_dir = os.path.join(uploads_root, workflow_id)
        os.makedirs(app_dir, exist_ok=True)

        # Create safe filename
        safe_doc_type = doc_type.replace(" ", "_")
        filename = f"{safe_doc_type}.pdf"
        file_path = os.path.join(app_dir, filename)

        # Save PDF
        pdf.output(file_path)

        public_url = f"/static/{workflow_id}/{filename}"

        print(f"[DocGenMCP] Generated '{doc_type}' -> {file_path}")

        return {
            "doc_type": doc_type,
            "file_path": file_path,
            "public_url": public_url,
            "loan_amount": loan_amount,
            "monthly_payment": monthly_payment,
            "generated_at": datetime.utcnow().isoformat()
        }


# =========================================
# Temporal Activity Functions
# =========================================

@activity.defn
async def generate_document(doc_type: str, data: dict, config: dict = None) -> dict:
    """Temporal Activity: Generate document via DocGenMCP"""
    return DocGenMCP.generate_document(doc_type, data, config or {})
