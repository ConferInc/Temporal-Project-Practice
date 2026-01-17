from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)

# We add text that the AI will try to read
pdf.cell(200, 10, txt="Loan Application Document", ln=1, align="C")
pdf.cell(200, 10, txt="Applicant Name: Shrikanth Test", ln=2)
pdf.cell(200, 10, txt="Annual Income: $55,000", ln=3)
pdf.cell(200, 10, txt="Credit Score: 610", ln=4) # Low score triggers Manager Review
pdf.cell(200, 10, txt="Employment: Junior AI Engineer", ln=5)

pdf.output("sample_loan.pdf")
print("Created sample_loan.pdf!")