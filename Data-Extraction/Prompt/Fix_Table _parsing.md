🎯 Exact Prompt: Credit Bureau Report Extraction Pipeline Fix

Context
The current extraction failure in the Credit Bureau Report pipeline is not caused by missing or incorrect extraction rules.
The extraction rules are comprehensive (553 lines) and correctly designed, but they are failing because the OCR layer only extracts ~5% of the document content, primarily headers and metadata, while ignoring structured tables.

As a result, downstream extraction rules have nothing to match against, leading to sparse canonical JSON and empty relational payloads.

🔴 Confirmed Root Cause (Do Not Misdiagnose)

The root cause is OCR engine configuration, not YAML rules, canonical assembly, or relational mapping.

Specifically:

OCR extracts only 19 lines from a 5-page PDF

Credit account (tradeline) tables are not captured

Payment history tables, consumer info tables, and credit score sections are missing from OCR output

~94% of extraction patterns fail because the expected text never appears in OCR results

✅ Primary Required Change (CRITICAL)

Upgrade the OCR stage to use table-aware, layout-preserving OCR, while keeping all downstream logic unchanged.

The OCR output must:

Preserve table structures (headers, rows, cells)

Include credit account / tradeline tables

Include payment history tables

Include consumer information tables

Expose structured text suitable for existing regex-based extraction rules

This change must be implemented before extraction rules are applied.

🧠 OCR Implementation Constraints (Very Important)

Prefer configuration changes over replacing libraries

Use OCR engines already present in the stack

Maintain existing OCR interfaces as much as possible

Fall back gracefully for documents without tables

Do not modify extraction rules to compensate for OCR failures

🛠 Approved OCR Approaches

Enable table-aware OCR using one of the following already-supported options:

DocTR with table/layout detection enabled

Dockling with table extraction features activated

The OCR stage must return structured output, not plain concatenated text.

🔁 Downstream Pipeline Behavior (Must Remain Unchanged)

After OCR enhancement:

Existing YAML-based extraction rules must run unchanged

Existing patterns should naturally begin matching newly available table content

Canonical JSON should populate with:

Consumer details

Credit accounts / tradelines

Liabilities

Credit summaries

Relational payload generation must:

Always include the complete payload schema

Populate extracted values where available

Set fields to null only when data is truly not present in the document

🟡 Secondary Fix (HIGH Priority, Small Scope)

Add explicit extraction rules for credit scores (e.g., FICO, bureau scores) to CreditBureauReport.yaml.

This is a real gap in the rules file but is not the primary cause of the current failure.

🟢 Success Criteria (Acceptance Conditions)

This change is successful if:

OCR output increases from ~5% to >80% of document content

Credit account and consumer tables appear in OCR output

Existing extraction rules match without modification

liabilities[] and related entities populate when data exists

Canonical JSON becomes materially complete (not metadata-only)

Relational payload remains schema-compliant and ingestion-ready

There must be no regression in:

Document classification

Metadata extraction

YAML-driven extraction behavior

🚫 Explicit Non-Goals (Do NOT Do These)

Do not redesign payload schema

Do not rewrite existing extraction rules

Do not infer or hallucinate missing values

Do not hardcode table parsing into YAML

Do not bypass canonical assembly

🧩 Intent Summary

This change fixes the OCR visibility layer, enabling the already-correct extraction rules to function as designed.
The objective is to expose tables and structured content to the extractor, not to redesign the extraction system.