You are provided with:

A document

A Markdown (.md) analysis file generated from a previous pipeline run, which documents:

Raw extracted text (OCR output)

Canonical JSON

Payload (relational) JSON

Missing fields, mismatches, and root-cause analysis

Use the Markdown file as the authoritative diagnostic reference for what is missing, why it is missing, and where in the pipeline the failure occurs.

🎯 Objective

Fix the pipeline so that:

All information that exists in the document and is extractable:

Appears in the canonical JSON

All fields defined by the database schema:

Always appear in the payload JSON

Are populated when values exist

Are explicitly set to null when values do not exist in the document

This must be achieved by improving pipeline behavior, not by manually patching outputs.

🔍 How to Use the Markdown File

The Markdown file explicitly identifies:

Fields present in raw extracted text but missing in canonical JSON

Fields present in canonical JSON but missing in payload JSON

Root causes (OCR limitation, extraction gap, mapping gap, schema constraint)

Use this information to:

Identify which pipeline layer is responsible (OCR, extraction rules, canonical assembly, relational mapping)

Apply fixes only at the responsible layer

🛠 Required Fixes (Apply as Needed)
1. Raw Text → Canonical JSON

If a value exists in raw extracted text but is missing in canonical JSON:

Fix the extraction logic so the value is captured

This may include:

Enabling table-aware OCR

Improving parsing of structured sections

Making extraction rules more robust

The canonical JSON must act as a complete, lossless structured representation of extracted document data.

2. Canonical JSON → Payload JSON

If a value exists in canonical JSON but is missing in payload JSON:

Determine whether the field exists in the database schema

Apply the following rules:

If the field exists in the schema:

Ensure it is always present in the payload JSON

Populate the value from canonical JSON or set it to null

If the field does not exist in the schema:

Its absence from the payload JSON is expected

Do not add it unless the schema is intentionally extended

🧾 Payload JSON Contract (Must Enforce)

Payload JSON must:

Always include the complete payload schema

Never silently drop schema-defined fields

Never omit a field due to missing extraction

Use null explicitly when data is not present in the document

🧠 Constraints (Very Important)

Do not modify document-specific outputs manually

Do not fabricate or infer values

Do not break existing YAML configurations

Do not change payload or database schema unless explicitly required

Fixes must be generic and reusable, not one-off

✅ Acceptance Criteria

The issue is considered fixed when:

Canonical JSON contains all extractable information from the document

Payload JSON contains all schema-defined fields for the document type

Fields missing from the document appear as null, not missing

No canonical field that maps to the schema is silently dropped

The comparison documented in the Markdown file no longer shows unexplained gaps

🧩 Intent Summary

The Markdown file explains what is broken and why.
Your task is to implement the fixes in the pipeline so these issues:

Are resolved for this document

Cannot silently occur again for future documents