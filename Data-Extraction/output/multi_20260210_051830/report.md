# Extraction Report
**File(s):** `chunk_000_LoanEstimate.pdf, chunk_001_LoanEstimate.pdf, chunk_002_LoanEstimate.pdf`
**Run:** 2026-02-10 05:18:30
**Mode:** multi-document
**Auto-split:** Yes

## Classification
- **Document Type:** Multi-document merge
- **Confidence:** 100%
- **Extraction Tool:** multi

## Extraction Results
- **Fields Extracted:** 33

## Validation Issues
- CRITICAL: Missing required field [deal.parties.0.individual.ssn] (Borrower SSN) - Document may be unclear.
- CRITICAL: Missing required field [deal.transaction_information.final_loan_amount] (Loan Amount) - Document may be unclear.
- CRITICAL: Missing required field [deal.collateral.subject_property.address] (Property Address) - Document may be unclear.

## Database Payload
- **Relational Payload:** 3 rows across 3 tables

## Performance
- **Elapsed:** 62.50s
- **Engine:** Deterministic Rule Engine (zero LLM)
