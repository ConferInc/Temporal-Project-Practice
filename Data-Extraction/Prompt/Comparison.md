You are given a folder containing multiple documents.
Each document must be processed individually through the extraction pipeline.

For each document, perform the following steps one by one:

1. Pipeline Execution

Run the document through the full extraction pipeline.

Capture the outputs for:

Document classification

Extracted payload JSON (schema-based extraction output)

Canonical JSON (expected normalized structure)

Relational / flattened JSON (used for database ingestion)

2. Field Coverage & Missing-Field Validation

Compare the payload JSON against the canonical JSON to determine:

Fields present and correctly extracted

Fields missing entirely from the payload

Fields present but null, empty, or partially extracted

Fields extracted at an incorrect JSON path

Compare the canonical JSON against the relational JSON to identify:

Canonical fields not represented in the relational output

Data loss or transformation issues during flattening

For each missing or incomplete field, record:

Canonical field name

JSON path

Expected data type or structure

Actual value found (or missing)

3. Issue Identification, Root Cause & Fix Recommendation

For each identified issue, explicitly document:

Issue

What is wrong (missing field, incorrect value, type mismatch, structure issue, etc.)

Why the issue occurred

Likely root cause, such as:

Extraction logic limitation

Classification error

Schema mismatch

Mapping / transformation gap

Document quality or format issue

How to fix the issue

Recommended corrective action, such as:

Extraction rule update

Schema or mapping change

Classification model adjustment

Pipeline logic enhancement

Document preprocessing improvement

⚠️ Do not apply fixes or modify any outputs — only document the recommendations.

4. Documentation (One Markdown File per Document)

Create a separate Markdown (.md) file for each document.
Name the file using the document identifier (e.g., document_name_pipeline_validation.md).

Each Markdown file must include the following sections:

Document Metadata

Document name

Document type / classification

Processing timestamp

Classification Results

Final classification label

Confidence score (if available)

Payload JSON (Extracted Output)

Summary of extracted fields

Full payload JSON (formatted)

Canonical JSON (Expected Output)

Full canonical JSON (formatted)

Relational / Ingestion JSON

Full relational / flattened JSON (formatted)

Missing & Mismatched Fields Analysis

Missing fields (present in canonical but absent in payload)

Incomplete fields (null / empty / partial values)

Extra or unexpected fields in the payload

Type mismatches

Structural mismatches

Use a clear table or bullet list including:

Field name

Canonical JSON path

Expected type

Payload value

Issue, Cause & Fix Summary

For each issue, include:

Issue description

Root cause

Recommended fix

Overall Validation Status

PASS / FAIL

Blocking issues

Summary notes

5. Constraints

Process documents independently — do not aggregate results.

Do not modify or auto-correct any outputs.

Do not infer or fabricate missing values.

Process all documents in the folder, generate one Markdown validation report per document, and confirm once the entire folder has been fully processed.