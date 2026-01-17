import os
import shutil
from fpdf import FPDF

# Ensure output directory exists
OUT_DIR = "test_data"
if os.path.exists(OUT_DIR):
    shutil.rmtree(OUT_DIR)
os.makedirs(OUT_DIR)

def create_doc(folder_name, doc_type, content_dict):
    """
    Creates a specific PDF doc inside a user's folder.
    doc_type: 'tax_return', 'id_card', 'pay_stub'
    """
    user_dir = os.path.join(OUT_DIR, folder_name)
    os.makedirs(user_dir, exist_ok=True)
    
    filename = f"{folder_name}_{doc_type}.pdf"
    path = os.path.join(user_dir, filename)
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    title = doc_type.replace("_", " ").upper()
    pdf.cell(200, 10, txt=title, ln=1, align="C")
    pdf.ln(10)
    
    # Content
    pdf.set_font("Arial", size=12)
    for key, value in content_dict.items():
        pdf.cell(200, 10, txt=f"{key}: {value}", ln=1)
        
    pdf.output(path)
    print(f"Created {path}")

# 1. Consistent & Good Applicant (Auto-Approve Candidate)
# Stated Income: 120k. Tax shows 120k.
create_doc("Alice_Perfect", "tax_return", {
    "Tax Year": "2024",
    "Name": "Alice Perfect",
    "SSN": "xxx-xx-1234",
    "Total Income": "$120,000",
    "Tax Paid": "$25,000"
})
create_doc("Alice_Perfect", "id_card", {
    "Name": "Alice Perfect",
    "DOB": "01/01/1990",
    "ID Number": "A12345678"
})
create_doc("Alice_Perfect", "pay_stub", {
    "Employer": "Tech Corp",
    "Pay Period": "Jan 2025",
    "Gross Pay": "$10,000" # Monthly * 12 = 120k
})

# 2. Inconsistent Applicant (Fraud/Risk Check)
# Stated Income will be HIGH, but Tax shows LOW.
create_doc("Bob_Liar", "tax_return", {
    "Tax Year": "2024",
    "Name": "Bob Liar",
    "SSN": "xxx-xx-9999",
    "Total Income": "$30,000", # LOW!
    "Tax Paid": "$2,000"
})
create_doc("Bob_Liar", "id_card", {
    "Name": "Bob Liar",
    "DOB": "05/05/1985",
    "ID Number": "B98765432"
})
create_doc("Bob_Liar", "pay_stub", {
    "Employer": "Pizza Place",
    "Pay Period": "Jan 2025",
    "Gross Pay": "$2,500" 
})

print("\n✅ Test Data Generation Complete. Check 'test_data/' folder.")
