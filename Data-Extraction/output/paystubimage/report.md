# Extraction Report
**File(s):** `paystubimage.pdf`
**Run:** 2026-02-10 14:29:23
**Mode:** nested
**Auto-split:** No

## Classification
- **Document Type:** DocumentType.PAY_STUBS
- **Confidence:** 95%
- **Extraction Tool:** parse_document_with_dockling

## Extraction Results
- **Fields Extracted:** 10

## Validation Issues
- CRITICAL: Missing required field [deal.parties.0.individual.ssn] (Borrower SSN) - Document may be unclear.
- CRITICAL: Missing required field [deal.transaction_information.final_loan_amount] (Loan Amount) - Document may be unclear.
- CRITICAL: Missing required field [deal.transaction_information.loan_purpose.value] (Loan Purpose) - Document may be unclear.
- CRITICAL: Missing required field [deal.collateral.subject_property.address] (Property Address) - Document may be unclear.
- QUALITY: parties[0].employment[0].employer_name is missing.

## Database Payload
- **Relational Payload:** 4 rows across 4 tables

## Performance
- **Elapsed:** 38.74s
- **Engine:** Deterministic Rule Engine (zero LLM)
