# Extraction Report
**File(s):** `example_bank_statement filled.pdf`
**Run:** 2026-02-10 05:21:28
**Mode:** nested
**Auto-split:** No

## Classification
- **Document Type:** DocumentType.BANK_STATEMENTS
- **Confidence:** 95%
- **Extraction Tool:** parse_document_with_dockling

## Extraction Results
- **Fields Extracted:** 39

## Validation Issues
- CRITICAL: Missing required field [deal.parties.0.individual.ssn] (Borrower SSN) - Document may be unclear.
- CRITICAL: Missing required field [deal.transaction_information.final_loan_amount] (Loan Amount) - Document may be unclear.
- CRITICAL: Missing required field [deal.transaction_information.loan_purpose.value] (Loan Purpose) - Document may be unclear.
- CRITICAL: Missing required field [deal.collateral.subject_property.address] (Property Address) - Document may be unclear.

## Database Payload
- **Relational Payload:** 4 rows across 4 tables

## Performance
- **Elapsed:** 35.05s
- **Engine:** Deterministic Rule Engine (zero LLM)
