from fpdf import FPDF

def create_pdf(filename, name, income, score):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="LOAN APPLICATION FORM", ln=1, align="C")
    pdf.cell(200, 10, txt=f"Applicant Name: {name}", ln=2)
    pdf.cell(200, 10, txt=f"Annual Income: ${income:,}", ln=3)
    pdf.cell(200, 10, txt=f"Credit Score: {score}", ln=4)
    pdf.cell(200, 10, txt="Address: 123 Tech Lane, Silicon Valley, CA", ln=5)
    pdf.output(filename)
    print(f"Created {filename}")

# 1. Good Application (Should Auto-Approve)
# Constraints: Score > 720, Income > 60,000
create_pdf("app_auto_approve.pdf", "Alice Wonder", 120000, 780)

# 2. Bad Application (Should Auto-Reject)
# Constraints: Score < 620
create_pdf("app_auto_reject.pdf", "Bob Failure", 45000, 500)

# 3. Uncertain Application (Should Wait for Manager)
# Constraints: 620 < Score < 720
create_pdf("app_manual_review.pdf", "Charlie Maybe", 55000, 680)
