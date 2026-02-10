# Extraction Report
**File(s):** `chunk_000_AppraisalForm1004.pdf, chunk_001_AppraisalForm1004.pdf, chunk_002_AppraisalForm1004.pdf`
**Run:** 2026-02-10 05:26:33
**Mode:** multi-document
**Auto-split:** Yes

## Classification
- **Document Type:** Multi-document merge
- **Confidence:** 100%
- **Extraction Tool:** multi

## Extraction Results
- **Fields Extracted:** 18

## Validation Issues
- CRITICAL: Missing required field [deal.parties.0.individual.ssn] (Borrower SSN) - Document may be unclear.
- CRITICAL: Missing required field [deal.transaction_information.final_loan_amount] (Loan Amount) - Document may be unclear.
- CRITICAL: Missing required field [deal.transaction_information.loan_purpose.value] (Loan Purpose) - Document may be unclear.

## Database Payload
- **Relational Payload:** 4 rows across 4 tables

## Performance
- **Elapsed:** 127.30s
- **Engine:** Deterministic Rule Engine (zero LLM)
