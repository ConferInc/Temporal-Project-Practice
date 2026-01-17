import os
import shutil
import random
from fpdf import FPDF

OUT_DIR = "test_data"

def create_simple_pdf(filename, content):
    """Creates a simple text-based PDF."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, content)
    pdf.output(filename)
    print(f"Created {filename}")

def create_credit_report(filename, applicant_name, score, history="Good payment history."):
    """Creates a realistic-looking Credit Report PDF."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "OFFICIAL CREDIT REPORT", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Report Date: 2024-01-15", ln=True)
    pdf.cell(0, 10, f"Reference #: {random.randint(100000, 999999)}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"Subject: {applicant_name}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 15, f"CREDIT SCORE: {score}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 10, f"Summary: {history}")
    pdf.ln(5)
    pdf.multi_cell(0, 10, "Details: No late payments in the last 24 months. Utilization is under 30%.")
    
    pdf.output(filename)
    print(f"Created {filename}")

if __name__ == "__main__":
    if os.path.exists(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR)

    PERSONAS = [
        {"name": "Alice_Perfect", "income": 120000, "stated_income": 120000, "credit_score": 780},
        {"name": "Bob_Liar", "income": 30000, "stated_income": 100000, "credit_score": 550},
        {"name": "Charlie_Manual", "income": 70000, "stated_income": 70000, "credit_score": 680}, # Score 620-740 hits Manual Review
    ]

    for p in PERSONAS:
        folder = os.path.join(OUT_DIR, p["name"])
        os.makedirs(folder, exist_ok=True)
        
        # Base Path for files
        # e.g. test_data/Alice_Perfect/Alice_Perfect
        base = os.path.join(folder, p["name"])
        app_name = p['name'].replace('_', ' ')
        
        # 1. Tax Return
        create_simple_pdf(
            f"{base}_tax_return.pdf", 
            f"TAX RETURN 2023\nName: {app_name}\nTotal Income: ${p['income']}\nTax Paid: ${p['income']*0.2}"
        )
        
        # 2. ID Card
        create_simple_pdf(
            f"{base}_id_card.pdf", 
            f"ID CARD\nName: {app_name}\nDOB: 01/01/1990\nID: {random.randint(10000,99999)}"
        )
        
        # 3. Pay Stub
        create_simple_pdf(
            f"{base}_pay_stub.pdf", 
            f"PAY STUB\nEmployee: {app_name}\nNet Pay: ${p['income']/26:.2f}\nPay Period: 01/01/2024 - 01/15/2024"
        )
        
        # 4. Credit Report
        create_credit_report(
            f"{base}_credit_report.pdf", 
            app_name, 
            p["credit_score"]
        )

    print("\n✅ Test Data Generation Complete. Check 'test_data/' folder.")
