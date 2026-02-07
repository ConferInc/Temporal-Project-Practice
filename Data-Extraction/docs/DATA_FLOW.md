# Data Flow & Transformations

This document details the data lifecycle through the Confer LOS pipeline, showing **input/output formats** at each stage and **transformation logic**.

---

## Pipeline Overview

```
Multi-page PDF Blob
    ↓
[1. Laundry] → Standardized PDF
    ↓
[2. Splitter] → List of Single-Page PDFs
    ↓
[3. Classifier] → Typed Pages (with metadata)
    ↓
[4. Rule Engine] → List of Flat Dictionaries
    ↓
[5. Merger] → Single Merged Dictionary
    ↓
[6. Assembler] → Nested Canonical JSON
    ↓
[7. MISMO Mapper] → MISMO 3.4 XML
```

---

## Stage 1: Pre-Processing Laundry

**Input:** Image file (JPEG, PNG, TIFF)

**Process:**
1. Detect file type (image vs. PDF)
2. If image: Run RapidOCR → Create PDF with embedded text layer
3. If PDF: Pass through unchanged

**Output:** PDF file (standardized format)

---

## Stage 2: Document Splitter

**Input:** Multi-page PDF

**Process:**
1. Open PDF with `pypdf`
2. Extract each page as separate PDF
3. Write to temp directory: `{original_name}_page_{N}.pdf`

**Output:** List of single-page PDF paths

**Example:**
```python
[
    "/tmp/loan_pkg_page_1.pdf",  # URLA Page 1
    "/tmp/loan_pkg_page_5.pdf",  # W-2 Form 2023
    "/tmp/loan_pkg_page_9.pdf",  # Bank Statement
]
```

---

## Stage 3: Classifier

**Input:** Single-page PDF

**Process:**
1. Extract text (first 3 pages via Doctr OCR)
2. Keyword scoring (1 point per match)
3. Regex scoring (3 points per match)
4. Calculate confidence: `min(0.5 + (score * 0.1), 0.95)`

**Output:** Classification result

**Example:**
```python
{
    "file_path": "/tmp/loan_pkg_page_5.pdf",
    "document_category": "W-2 Form",
    "confidence": 0.85,
    "reasoning": "Found keywords: 'Form W-2', 'Wages, tips', regex match: 'Employer\\'s EIN'"
}
```

---

## Stage 4: Rule Engine (Zero-LLM Extraction)

**Input:** Single-page PDF + YAML rules file

**Process:**
1. Load document-type-specific YAML rules (e.g., `rules/w2.yaml`)
2. Extract text via Doctr OCR
3. Apply regex patterns from rules
4. Extract field values
5. Convert data types (currency, date, boolean)

**Output:** Flat dictionary

**Example Rule File** (`rules/w2.yaml`):
```yaml
document_type: "W-2 Form"
priority: 10  # Highest (IRS verified)

rules:
  - field: "wages"
    canonical_path: "deal.parties[0].employment[0].income.base_amount"
    pattern: "Wages, tips, other compensation\\s*\\$?([\\d,]+\\.\\d{2})"
    extraction_type: "regex"
    data_type: "currency"
    required: true

  - field: "borrower_ssn"
    canonical_path: "deal.parties[0].individual.ssn"
    pattern: "Employee's social security number[:\\s]*(\\d{3}-\\d{2}-\\d{4})"
    extraction_type: "regex"
    data_type: "string"
    required: true
```

**Example Output:**
```python
{
    "wages": 75000.00,
    "employer_name": "Acme Corporation",
    "employer_ein": "12-3456789",
    "borrower_ssn": "123-45-6789",
    "tax_year": 2023,
    "_metadata": {
        "document_type": "W-2 Form",
        "priority": 10,
        "page_number": 5
    }
}
```

---

## Stage 5: Merger (Priority Logic + Identity Resolution)

**Input:** List of flat dictionaries (one per page/document)

**Process:**
1. **Identity Resolution:** Group documents by borrower (SSN match)
2. **Priority Resolution:** For conflicting fields, use highest-priority source
3. **Array Aggregation:** Combine multi-value fields (employment, assets)

**Output:** Single merged dictionary

### Priority Matrix

| Document Type | Priority | Trust Level |
|---------------|----------|-------------|
| W-2 Form | 10 | IRS Verified |
| Tax Return (1040) | 9 | IRS Filed |
| Pay Stub | 7 | Employer Issued |
| Bank Statement | 6 | Bank Verified |
| URLA (Form 1003) | 3 | Self-Reported |

### Merge Example

**Input:** 3 documents for same borrower
```python
doc1 = {
    "borrower_ssn": "123-45-6789",
    "wages": 75000.00,  # From W-2 (priority 10)
    "_metadata": {"document_type": "W-2 Form", "priority": 10}
}

doc2 = {
    "borrower_ssn": "123-45-6789",
    "declared_income": 80000.00,  # From URLA (priority 3)
    "loan_amount": 350000.00
}
```

**Output:** Merged dictionary
```python
{
    "borrower_ssn": "123-45-6789",
    "verified_income": 75000.00,  # W-2 wins (priority 10 > 3)
    "declared_income": 80000.00,  # Preserved for audit
    "loan_amount": 350000.00,
    "_metadata": {
        "primary_income_source": {"document": "W-2 Form", "priority": 10},
        "conflicts_resolved": [{
            "field": "income",
            "w2_value": 75000,
            "urla_value": 80000,
            "winner": "w2"
        }]
    }
}
```

---

## Stage 6: Canonical Assembler (Flat → Nested)

**Input:** Flat merged dictionary

**Process:**
1. Load canonical schema (`schema.json`)
2. Parse field paths (dot notation with array indices)
3. Create nested structure
4. Validate enums (strict matching)
5. Apply defaults (`null` for missing fields)

**Output:** Nested canonical JSON

### Path Mapping

| Flat Key | Canonical Path |
|----------|----------------|
| `borrower_first_name` | `deal.parties[0].individual.first_name` |
| `wages` | `deal.parties[0].employment[0].income.base_amount` |
| `account_balance` | `deal.assets[0].account_balance` |

### Transformation Example

**Input (Flat):**
```python
{
    "borrower_first_name": "John",
    "borrower_ssn": "123-45-6789",
    "verified_income": 75000.00,
    "loan_purpose": "Purchase"
}
```

**Output (Nested Canonical JSON):**
```json
{
    "document_metadata": {
        "schema_version": "3.4.0"
    },
    "deal": {
        "transaction_information": {
            "loan_purpose": {
                "value": "Purchase",
                "options": ["Purchase", "Refinance", "Construction", "Other"]
            }
        },
        "parties": [{
            "party_role": {
                "value": "Borrower",
                "options": ["Borrower", "CoBorrower"]
            },
            "individual": {
                "first_name": "John",
                "ssn": "123-45-6789"
            },
            "employment": [{
                "income": {
                    "base_amount": 75000.00
                }
            }]
        }]
    }
}
```

---

## Stage 7: MISMO Mapper (Canonical → XML)

**Input:** Nested canonical JSON

**Process:**
1. Load MISMO mapping rules (98 XPath mappings)
2. Traverse canonical JSON structure
3. For each field, lookup XPath target
4. Handle array indices (0-indexed → 1-indexed)
5. Generate XML using ElementTree

**Output:** MISMO 3.4 XML string

### XML Output Example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<MESSAGE xmlns="http://www.mismo.org/residential/2009/schemas">
    <DEAL_SETS>
        <DEAL_SET>
            <DEALS>
                <DEAL>
                    <PARTIES>
                        <PARTY SequenceNumber="1">
                            <INDIVIDUAL>
                                <NAME>
                                    <FirstName>John</FirstName>
                                </NAME>
                                <TAXPAYER_IDENTIFIERS>
                                    <TAXPAYER_IDENTIFIER>
                                        <TaxpayerIdentifierValue>123-45-6789</TaxpayerIdentifierValue>
                                    </TAXPAYER_IDENTIFIER>
                                </TAXPAYER_IDENTIFIERS>
                            </INDIVIDUAL>
                        </PARTY>
                    </PARTIES>
                </DEAL>
            </DEALS>
        </DEAL_SET>
    </DEAL_SETS>
</MESSAGE>
```

---

## Data Type Transformations

| Type | Input Format | Canonical Format | MISMO Format |
|------|--------------|------------------|--------------|
| **Currency** | "$75,000.00" | 75000.00 (float) | "75000.00" |
| **Date** | "06/15/1985" | "1985-06-15" (ISO) | "1985-06-15" |
| **SSN** | "123-45-6789" | "123-45-6789" | "123-45-6789" |
| **Boolean** | "Yes" / "No" | true / false | "true" / "false" |
| **Enum** | "Refi" | "Refinance" | "Refinance" |

---

## Error Handling

### Missing Required Fields
```python
{
    "field": "wages",
    "value": null,
    "error": "Required field not found in document",
    "confidence": 0.0
}
```

### Enum Validation Failures
```python
{
    "loan_purpose": {
        "value": null,
        "extracted_raw": "Refi-Purchase",
        "error": "No valid enum match",
        "options": ["Purchase", "Refinance", "Construction", "Other"]
    }
}
```

---

## Performance Metrics (Target)

| Stage | Avg Time | Max Time | Throughput |
|-------|----------|----------|------------|
| Laundry | 0.5s | 2s | 120 pages/min |
| Splitter | 0.1s | 0.5s | 600 pages/min |
| Classifier | 0.3s | 1s | 200 pages/min |
| Rule Engine | 0.8s | 3s | 75 pages/min |
| Merger | 0.2s | 1s | 300 loans/min |
| Assembler | 0.1s | 0.5s | 600 loans/min |
| MISMO Mapper | 0.2s | 1s | 300 loans/min |
| **Total Pipeline** | **2.2s** | **9s** | **27 loans/min** |

*(Benchmarks to be validated in Phase 3)*
