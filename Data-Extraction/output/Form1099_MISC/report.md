# Extraction Report
**File(s):** `Form1099_MISC.pdf`
**Run:** 2026-02-10 15:58:48
**Mode:** nested
**Auto-split:** No

## Classification
- **Document Type:** DocumentType.FORM_1099_MISC
- **Confidence:** 95%
- **Extraction Tool:** ocr_document

## Extraction Results
- **Fields Extracted:** 9

## Validation Issues
- CRITICAL: Missing required field [deal.parties.0.individual.full_name] (Borrower Name) - Document may be unclear.
- CRITICAL: Missing required field [deal.parties.0.individual.ssn] (Borrower SSN) - Document may be unclear.
- CRITICAL: Missing required field [deal.transaction_information.final_loan_amount] (Loan Amount) - Document may be unclear.
- CRITICAL: Missing required field [deal.transaction_information.loan_purpose.value] (Loan Purpose) - Document may be unclear.
- CRITICAL: Missing required field [deal.collateral.subject_property.address] (Property Address) - Document may be unclear.

## Database Payload
- **Relational Payload:** 5 rows across 3 tables

## Performance
- **Elapsed:** 18.20s
- **Engine:** Deterministic Rule Engine (zero LLM)
