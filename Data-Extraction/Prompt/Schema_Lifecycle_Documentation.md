# Payload Schema Lifecycle Documentation

This document provides a comprehensive explanation of the payload schema architecture in the Data Extraction Pipeline, answering the key questions about schema source, consistency, and lifecycle.

---

## 1. Source of the Payload Schema

### Overview
The payload schema is **derived from multiple sources** working in concert through a **two-stage extraction architecture**:

### Schema Sources

#### A. YAML Rule Files (Primary Source)
- **Location**: `src/rules/` directory
- **Purpose**: Define document-type-specific extraction patterns
- **Format**: YAML configuration files (one per document type)

**Examples**:
- `PayStub.yaml` - Pay stub extraction rules
- `W-2Form.yaml` - W-2 form extraction rules
- `URLA.yaml` - URLA Form 1003 extraction rules
- `BankStatement.yaml` - Bank statement extraction rules
- `LoanEstimate.yaml` - Loan Estimate H-24 extraction rules

**YAML Rule Structure**:
```yaml
document_type: "Pay Stub"
schema_version: "1.0"

rules:
  - id: employer_name_heading
    type: heading
    level: 2
    key: "paystub_employer_name"                                    # Flat mode key
    target_path: "deal.parties[0].employment[0].employer_name"      # Nested canonical path
    
  - id: ytd_gross_amount
    type: table
    extract_keys:
      "deal.parties[0].income_verification_fragments[0].ytd_gross_amount": "paystub_ytd_gross_amount"
```

**Key Characteristics**:
- Each rule specifies BOTH:
  - `key`: Business key for flat extraction mode
  - `target_path`: Nested path in canonical schema
- Rule types supported:
  - `heading`: Extract from markdown headings
  - `key_value`: Extract key-value pairs
  - `table`: Extract from markdown tables
  - `regex`: Pattern-based extraction
  - `checkbox`: OCR checkbox detection
  - `positional`: Anchor-based extraction
  - `section`: Section-based extraction
  - `static`: Inject constant values
  - `computed`: Copy/transform existing values

#### B. Canonical Schema Template (Target Structure)
- **Location**: `schemas/canonical_schema/schema.json`
- **Purpose**: Defines the unified MISMO 3.4-aligned structure
- **Format**: JSON schema with nested hierarchy

**Structure**:
```json
{
  "document_metadata": {
    "schema_version": "3.4.0",
    "delivery_standard": "Fannie Mae Selling Guide / ILAD",
    "audit_trail_enabled": true
  },
  "deal": {
    "identifiers": {...},
    "transaction_information": {...},
    "parties": [{
      "party_role": {...},
      "individual": {...},
      "employment": [...],
      "income_verification_fragments": [...]
    }],
    "assets": [...],
    "liabilities": [...],
    "collateral": {...},
    "underwriting_and_compliance": {...},
    "disclosures_and_closing": {...}
  }
}
```

#### C. Document-Specific Canonical Mappings (Optional)
- **Location**: `schemas/canonical_mappings/`
- **Purpose**: Provide explicit field-to-path mappings (legacy support)
- **Format**: JSON array of mapping rules

**Example** (`PayStub.json`):
```json
[
  {
    "sourceField": "employerName",
    "targetPath": "deal.parties[0].employment[0].employer_name",
    "priority": 1
  },
  {
    "sourceField": "ytdGrossAmount",
    "targetPath": "deal.parties[0].income_verification_fragments[0].ytd_gross_amount",
    "priority": 1
  }
]
```

#### D. MISMO 3.4 Mapping Configuration
- **Location**: `schemas/mismo_mapping/map_mismo_3_6.json`
- **Purpose**: Maps canonical JSON to MISMO 3.4 XML output
- **Contains**: 98 deterministic XPath mappings

### Two-Stage Extraction Architecture

The payload schema is generated through a **deterministic two-stage process**:

**Stage 1: Flat Extraction** (Rule Engine)
```
Input: Raw text/markdown → Rule Engine (YAML rules) → Flat Dictionary
Example Output: {
  "paystub_employer_name": "Acme Corp",
  "paystub_ytd_gross_amount": 75000.00,
  "paystub_employee_name": "John Doe"
}
```

**Stage 2: Canonical Assembly** (Canonical Assembler)
```
Input: Flat Dictionary → Canonical Assembler (Strategies) → Nested Canonical JSON
Example Output: {
  "deal": {
    "parties": [{
      "individual": {"full_name": "John Doe"},
      "employment": [{"employer_name": "Acme Corp"}],
      "income_verification_fragments": [{"ytd_gross_amount": 75000.00}]
    }]
  }
}
```

### Implementation Files
1. **Rule Engine**: `src/mapping/rule_engine.py`
   - Reads YAML rules from `src/rules/`
   - Supports `output_mode="flat"` or `output_mode="nested"`
   - Zero-LLM, deterministic extraction

2. **Canonical Assembler**: `src/mapping/canonical_assembler.py`
   - Document-type-specific strategies
   - Transforms flat dictionaries to nested canonical JSON
   - Multi-party resolution for merged documents

3. **Unified Extraction**: `src/logic/unified_extraction.py`
   - Orchestrates the two-stage pipeline
   - Handles single and multi-document processing

---

## 2. Schema Consistency Across Documents

### Answer: **Variable Schema with Unified Canonical Target**

The payload schema **varies by document type** during extraction, but **converges to a unified canonical structure**.

### Document-Specific Extraction Schemas

Each document type has its own extraction schema defined by its YAML rule file:

| Document Type | YAML Rule File | Flat Key Prefix | Unique Fields |
|---------------|----------------|-----------------|---------------|
| W-2 Form | `W-2Form.yaml` | `w2_` | `w2_wages_annual`, `w2_federal_tax_withheld`, `w2_employer_ein` |
| Pay Stub | `PayStub.yaml` | `paystub_` | `paystub_current_gross_pay`, `paystub_ytd_gross_amount` |
| URLA (Form 1003) | `URLA.yaml` | `urla_` | `urla_loan_purpose`, `urla_mortgage_type`, `urla_property_address` |
| Bank Statement | `BankStatement.yaml` | `bank_` | `bank_account_number`, `bank_ending_balance`, `bank_deposit_transactions` |
| Loan Estimate | `LoanEstimate.yaml` | `le_` | `le_total_closing_costs`, `le_apr`, `le_rate_lock` |
| Tax Return 1040 | `TaxReturn.yaml` | `tax_` | `tax_adjusted_gross_income`, `tax_filing_status` |
| Appraisal 1004 | `Appraisal.yaml` | `appraisal_` | `appraisal_property_address`, `appraisal_contract_price` |

### Schema Selection Process

**Determinant: Document Classification**

The extraction schema is selected through a deterministic classification pipeline:

```
Input Document → Classifier (src/logic/classifier.py)
  ↓
Classification Decision: {
  "document_category": "Pay Stub",
  "confidence": 0.95,
  "recommended_tool": "parse_document_with_dockling"
}
  ↓
Rule Engine loads: src/rules/PayStub.yaml
  ↓
Extraction uses: paystub_* flat keys
```

**Classification Logic** (`src/logic/classifier.py`):
1. Extract text from first 3 pages (Doctr OCR)
2. Keyword scoring (1 point per match)
3. Regex scoring (3 points per match)
4. Confidence calculation: `min(0.5 + (score * 0.1), 0.95)`

**Filename Mapping** (`src/mapping/rule_engine.py`):
```python
_ALIASES = {
    "W-2 Form": "W-2Form",
    "Tax Return (1040)": "TaxReturn",
    "Appraisal (Form 1004)": "Appraisal",
    "Loan Estimate (H-24)": "LoanEstimate",
    "Government ID": "DriversLicense",
    "Form 1099-MISC": "Form1099_MISC",
    "Credit Bureau Report": "CreditBureauReport",
}
```

### Unified Canonical Schema

**All document types map to the same canonical structure**:

**Canonical Assembler Strategies** (`src/mapping/canonical_assembler.py`):
```python
_STRATEGIES = {
    "W-2 Form": _w2_strategy,
    "URLA (Form 1003)": _urla_strategy,
    "Pay Stub": _paystub_strategy,
    "Bank Statement": _bank_statement_strategy,
    "Tax Return (1040)": _tax_return_strategy,
    "Appraisal (Form 1004)": _appraisal_strategy,
    "Loan Estimate": _loan_estimate_strategy,
    "merged": _merged_strategy,  # Multi-document merge
}
```

Each strategy knows how to:
1. Map document-specific flat keys to canonical paths
2. Build nested party/employment/asset structures
3. Handle document-specific enums and data types

**Example Mapping**:
```
Pay Stub Flat Key              → Canonical Path
-------------------              -----------------
paystub_employer_name           → deal.parties[0].employment[0].employer_name
paystub_ytd_gross_amount        → deal.parties[0].income_verification_fragments[0].ytd_gross_amount

W-2 Flat Key                   → Canonical Path
------------                   → -----------------
w2_employer_name                → deal.parties[0].employment[0].employer_name
w2_wages_annual                 → deal.parties[0].income_verification_fragments[0].w2_wages_annual
```

### Multi-Document Merging

**When multiple documents are processed together**:

1. **Identity Resolution** (SSN exact match, name fuzzy match ≥80%)
2. **Priority-Based Conflict Resolution**:
   | Document Type | Priority | Trust Level |
   |---------------|----------|-------------|
   | W-2 Form | 10 | IRS Verified |
   | Tax Return (1040) | 9 | IRS Filed |
   | Pay Stub | 7 | Employer Issued |
   | Bank Statement | 6 | Bank Verified |
   | URLA (Form 1003) | 3 | Self-Reported |

3. **Multi-Party Clustering** (`_merged_strategy`):
   - Scans all flat keys for identity prefixes
   - Clusters by SSN/name similarity
   - Builds one canonical party per cluster
   - Aggregates employment/income data across documents

---

## 3. Schema Lifecycle & Validation

### Lifecycle Stages

The payload schema is **validated and enforced at 5 distinct stages** in the pipeline:

#### Stage 1: Classification & Routing
**File**: `src/logic/classifier.py`
**When**: Before extraction begins
**What**: Document type validation
```python
{
  "document_category": "Pay Stub",
  "confidence": 0.95,
  "reasoning": "Found keywords: 'Employee Name', 'Pay Period'"
}
```
**Failure Handling**: Falls back to generic extraction if confidence < 0.5

#### Stage 2: Rule-Based Extraction
**File**: `src/mapping/rule_engine.py`
**When**: During flat extraction
**What**: 
- YAML rule syntax validation
- Regex pattern matching
- Data type coercion (currency, dates, enums)
```python
# Transform definitions in YAML rules
transform: "annual_to_monthly"  # Divides by 12
transform: "to_float"            # Converts to currency
transform: "strip_ocr_noise"     # Cleans OCR artifacts
```
**Failure Handling**: 
- Missing fields → skipped silently
- Invalid regex → logged as warning
- Type coercion failures → raw string preserved

#### Stage 3: Canonical Assembly
**File**: `src/mapping/canonical_assembler.py`
**When**: After flat extraction, before validation
**What**:
- Document-specific strategy selection
- Nested structure construction
- Array indexing validation
- Enum value mapping
```python
# Enum validation example
if flat.get("urla_loan_purpose"):
    # Must match canonical schema options: ["Purchase", "Refinance", "Construction", "Other"]
    tx["loan_purpose"] = {"value": flat["urla_loan_purpose"]}
```
**Failure Handling**:
- Invalid paths → field skipped
- Missing required sections → empty dict created
- Unknown document type → falls back to `_generic_strategy`

#### Stage 4: Data Validation
**File**: `src/logic/validator.py`
**When**: After canonical assembly
**What**:
- Enum strict matching
- Required field checks
- Data type validation
- Cross-field consistency checks
```python
validator = DataValidator()
canonical_data, validation_errors = validator.validate(canonical_data)

# Example errors:
[
  "Field 'loan_purpose' has invalid enum value 'Refi-Purchase'. Expected: ['Purchase', 'Refinance', 'Construction', 'Other']",
  "Required field 'borrower_ssn' is missing",
  "Field 'interest_rate' expected type float, got string '3.5%'"
]
```
**Failure Handling**:
- Validation errors are **logged but non-blocking**
- Invalid fields are preserved with `null` values
- Errors are included in `report.md` output

#### Stage 5: Relational Transformation
**File**: `src/mapping/relational_transformer.py`
**When**: Before database ingestion
**What**:
- Flattens nested canonical JSON to relational tables
- Foreign key generation
- Table schema validation
```python
rt = RelationalTransformer()
relational_payload = rt.transform(canonical_data)

# Output: Database-ready payload
{
  "parties": [...],           # Flat party rows
  "employment": [...],        # Flat employment rows
  "assets": [...],            # Flat asset rows
  "_metadata": {
    "total_rows": 15,
    "table_count": 5
  }
}
```
**Failure Handling**:
- Unmapped fields → logged as warnings
- Schema mismatches → field skipped
- Foreign key violations → orphan record logged

### Non-Conforming Document Handling

**What happens if a document does not fully conform to the expected schema?**

#### Scenario 1: Missing Required Fields
```
Document: Pay Stub missing "ytd_gross_amount"
```
**Behavior**:
1. Rule Engine attempts extraction using YAML pattern
2. If not found, field is absent from flat dict
3. Canonical Assembler skips the field
4. Validator logs: `"Field 'ytd_gross_amount' is missing"`
5. Relational Transformer inserts `NULL` in database

**Output**:
```json
{
  "deal": {
    "parties": [{
      "income_verification_fragments": [{
        "ytd_gross_amount": null  // Missing field
      }]
    }]
  }
}
```

#### Scenario 2: Invalid Enum Values
```
Document: URLA with loan_purpose = "Refi-Purchase"
```
**Behavior**:
1. Rule Engine extracts raw value: `"Refi-Purchase"`
2. Canonical Assembler attempts enum mapping, fails
3. Validator logs error: `"Invalid enum value 'Refi-Purchase'. Expected: ['Purchase', 'Refinance', 'Construction', 'Other']"`
4. Field is set to `null` with error metadata

**Output**:
```json
{
  "loan_purpose": {
    "value": null,
    "extracted_raw": "Refi-Purchase",
    "error": "No valid enum match",
    "options": ["Purchase", "Refinance", "Construction", "Other"]
  }
}
```

#### Scenario 3: OCR Extraction Failures
```
Document: Scanned PDF with poor quality
```
**Behavior**:
1. Classifier routes to Doctr OCR
2. If text extraction yields < 50 characters, triggers OCR fallback
3. Rule Engine applies regex with relaxed matching
4. Fields with low confidence are flagged
5. Validation logs quality warnings

**Code** (`src/logic/unified_extraction.py`):
```python
_MIN_TEXT_LENGTH = 50

if result.get("_raw_text_length", 0) < _MIN_TEXT_LENGTH:
    logger.warning(f"Low text yield ({result['_raw_text_length']} chars), retrying with OCR...")
    result = unified_extract(file_path, output_mode="flat", force_ocr=True)
```

#### Scenario 4: Unknown Document Type
```
Document: Unrecognized form
```
**Behavior**:
1. Classifier returns `"document_category": "Unknown"` with low confidence
2. Rule Engine cannot find matching YAML file
3. Canonical Assembler uses `_generic_strategy`
4. All flat keys are dumped to `"flat_data"` section

**Output**:
```json
{
  "deal": {},
  "flat_data": {
    "field1": "value1",
    "field2": "value2"
  }
}
```

### Validation Enforcement Points

| Stage | File | Enforcement Type | Blocking? |
|-------|------|------------------|-----------|
| Classification | `classifier.py` | Document type check | No (fallback to generic) |
| Extraction | `rule_engine.py` | Regex validation, data type coercion | No (skips invalid fields) |
| Assembly | `canonical_assembler.py` | Path validation, enum mapping | No (uses null for invalid) |
| Validation | `validator.py` | Enum strict check, required fields | **No** (logs errors only) |
| Transformation | `relational_transformer.py` | Table schema validation | No (skips unmapped fields) |

**Key Principle**: **Non-Blocking Validation**
- Pipeline never fails due to schema violations
- All errors are logged and reported
- Partial extraction is preferred over complete failure
- Audit trail preserved in `report.md`

### Validation Output

**Report File** (`output/{document}/report.md`):
```markdown
# Extraction Report
**File(s):** `paystub.pdf`
**Run:** 2026-02-10 14:35:22
**Mode:** nested

## Classification
- **Document Type:** Pay Stub
- **Confidence:** 95%
- **Extraction Tool:** parse_document_with_dockling

## Extraction Results
- **Fields Extracted:** 32

## Validation Issues
- Field 'ytd_gross_amount' is missing
- Field 'employment_status' has invalid enum value 'Active'. Expected: ['Current', 'Previous']

## Database Payload
- **Relational Payload:** 8 rows across 3 tables

## Performance
- **Elapsed:** 2.45s
- **Engine:** Deterministic Rule Engine (zero LLM)
```

---

## Summary

### 1. Source of Payload Schema
**Answer**: The payload schema is derived from **YAML rule files** (`src/rules/*.yaml`) that define document-type-specific extraction patterns, combined with a **unified canonical schema template** (`schemas/canonical_schema/schema.json`). The two-stage architecture (flat extraction → canonical assembly) uses these sources to generate the final payload.

### 2. Schema Consistency Across Documents
**Answer**: The payload schema **varies by document type** during extraction (determined by classifier-based routing to specific YAML rule files), but **all documents converge to the same canonical structure** through document-specific assembler strategies. Multi-document processing uses priority-based merging and identity resolution.

### 3. Schema Lifecycle
**Answer**: The payload schema is **validated at 5 stages** (classification, extraction, assembly, validation, transformation) but **never blocks processing**. Non-conforming documents are handled gracefully with null values, error logging, and fallback strategies. Validation errors are reported in `report.md` but do not halt the pipeline.

---

## Key Design Principles

1. **Deterministic Processing**: Zero-LLM, YAML-driven rules ensure reproducibility
2. **Non-Blocking Validation**: Partial extraction preferred over complete failure
3. **Document-Specific Flexibility**: Each document type has tailored extraction rules
4. **Unified Canonical Target**: All documents map to MISMO 3.4-aligned structure
5. **Audit Compliance**: Full error logging and reporting for compliance tracking
6. **Graceful Degradation**: Unknown documents fall back to generic extraction

---

## References

### Key Files
- **Rule Engine**: `src/mapping/rule_engine.py`
- **Canonical Assembler**: `src/mapping/canonical_assembler.py`
- **Unified Extraction**: `src/logic/unified_extraction.py`
- **Classifier**: `src/logic/classifier.py`
- **Validator**: `src/logic/validator.py`
- **Relational Transformer**: `src/mapping/relational_transformer.py`
- **Main Pipeline**: `main.py`

### Configuration Files
- **YAML Rules**: `src/rules/`
- **Canonical Schema**: `schemas/canonical_schema/schema.json`
- **Canonical Mappings**: `schemas/canonical_mappings/`
- **MISMO Mapping**: `schemas/mismo_mapping/map_mismo_3_6.json`

### Documentation
- **Architecture**: `docs/ARCHITECTURE.md`
- **Data Flow**: `docs/DATA_FLOW.md`
- **Task Log**: `docs/TASK_LOG.md`
