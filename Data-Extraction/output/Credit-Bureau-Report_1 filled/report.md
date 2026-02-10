# Extraction Report
**File(s):** `Credit-Bureau-Report_1 filled.pdf`
**Run:** 2026-02-10 06:23:39
**Mode:** nested
**Auto-split:** No

## Classification
- **Document Type:** DocumentType.CREDIT_BUREAU_REPORT
- **Confidence:** 95%
- **Extraction Tool:** parse_document_with_dockling

## Extraction Results
- **Fields Extracted:** 47

## Validation Issues
- CRITICAL: Missing required field [deal.parties.0.individual.full_name] (Borrower Name) - Document may be unclear.
- CRITICAL: Missing required field [deal.transaction_information.final_loan_amount] (Loan Amount) - Document may be unclear.
- CRITICAL: Missing required field [deal.transaction_information.loan_purpose.value] (Loan Purpose) - Document may be unclear.
- CRITICAL: Missing required field [deal.collateral.subject_property.address] (Property Address) - Document may be unclear.

## Database Payload
- **Relational Payload:** 4 rows across 4 tables

## Performance
- **Elapsed:** 197.84s
- **Engine:** Deterministic Rule Engine (zero LLM)
