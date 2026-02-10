# Extraction Report
**File(s):** `W2_Form1 filled.pdf`
**Run:** 2026-02-10 05:03:15
**Mode:** nested
**Auto-split:** No

## Classification
- **Document Type:** DocumentType.W2_FORMS
- **Confidence:** 95%
- **Extraction Tool:** parse_document_with_dockling

## Extraction Results
- **Fields Extracted:** 25

## Validation Issues
- CRITICAL: Missing required field [deal.transaction_information.final_loan_amount] (Loan Amount) - Document may be unclear.
- CRITICAL: Missing required field [deal.transaction_information.loan_purpose.value] (Loan Purpose) - Document may be unclear.
- CRITICAL: Missing required field [deal.collateral.subject_property.address] (Property Address) - Document may be unclear.

## Database Payload
- **Relational Payload:** 6 rows across 6 tables

## Performance
- **Elapsed:** 39.00s
- **Engine:** Deterministic Rule Engine (zero LLM)
