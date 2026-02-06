# 📋 Canonical Model Quick Reference

## One-Page Cheat Sheet

---

## Schema Sections Overview

| Section | Purpose | Used By |
|---------|---------|---------|
| **transaction** | Bank account & transactions | Bank Statement |
| **borrower** | Basic borrower info | Bank Statement, Gov ID |
| **deal** | Application metadata | URLA |
| **loan** | Loan details | URLA |
| **parties** | Detailed party info | URLA, Gov ID |
| **employment** | Employment history | URLA, Pay Stub |
| **financials** | Income/Assets/Liabilities | URLA, Pay Stub, Bank Statement |
| **collateral** | Property information | URLA, Sales Contract |
| **governmentLoans** | VA/FHA loan details | URLA, VA Forms |
| **closing** | Closing information | URLA, Closing Disclosure |

---

## Document Type Scoping

```python
DOCUMENT_SCOPE = {
    "BankStatement": {"transaction", "borrower"},
    "PayStub": {"financials.incomes", "employment"},
    "W2": {"financials.incomes"},
    "URLA": {"deal", "loan", "parties", "employment", "financials", "collateral", "governmentLoans", "closing"},
    "GovernmentID": {"parties"},
    "SalesContract": {"collateral"},
    "PropertyAppraisal": {"collateral"},
    "TaxReturn": {"financials.incomes"},
    "CreditReport": {"financials.liabilities"}
}
```

---

## Mapping Rule Format

### Standard Field Mapping
```json
{
  "sourceField": "extractedFieldName",
  "targetPath": "canonical.path[0].field",
  "priority": 1
}
```

### List Pattern Mapping
```json
{
  "type": "listPattern",
  "targetPath": "transaction.list",
  "sourcePrefix": "deposits",
  "priority": 1,
  "itemMapping": {
    "amount": "amount",
    "date": "date",
    "description": "description"
  }
}
```

---

## Priority Rules

- **Lower number = Higher priority**
- **First match wins** (deterministic)
- **No default values** (data purity)

Example:
```json
[
  {"sourceField": "institutionName", "priority": 1},  // Try this first
  {"sourceField": "bankName", "priority": 2}          // Fallback if #1 not found
]
```

---

## Pipeline Flow

```
1. Classify Document
   ↓
2. Extract Raw Content (docTR/Dockling)
   ↓
3. Structure Extraction (LLM → Key-Value JSON)
   ↓
4. Canonical Mapping (Rule-Based, NO LLM)
   ↓
5. Normalization (Future: dates, currency, enums)
   ↓
6. Output: Partial Canonical JSON
```

---

## Key Principles

✅ **Deterministic**: Same input → Same output  
✅ **Scoped**: Only allowed sections populated  
✅ **Partial**: No empty initialization  
✅ **Pure**: No LLM in mapping, no defaults  
✅ **MISMO-Ready**: Aligned with industry standards

---

## File Locations

| Component | Path |
|-----------|------|
| Schema | `resources/canonical_schema/schema.json` |
| Mapper | `tools/canonical_mapper.py` |
| BankStatement Rules | `resources/canonical_mappings/BankStatement.json` |
| PayStub Rules | `resources/canonical_mappings/PayStub.json` |
| URLA Rules | `resources/canonical_mappings/URLA.json` |
| GovernmentID Rules | `resources/canonical_mappings/GovernmentID.json` |

---

## Common Patterns

### Nested Object Path
```
"targetPath": "parties[0].individual.firstName"
```

### Array Indexing
```
"targetPath": "financials.incomes[0].amount"
```

### Multi-Level Nesting
```
"targetPath": "collateral.subjectProperty.address.street"
```

---

## Example: Bank Statement

**Input**:
```json
{
  "institutionName": "Chase",
  "currentBalance": 25000,
  "deposits_1_amount": 5000,
  "deposits_1_date": "2024-01-15"
}
```

**Output**:
```json
{
  "transaction": {
    "assets": [{
      "institutionName": "Chase",
      "currentBalance": 25000
    }],
    "list": [{
      "amount": 5000,
      "date": "2024-01-15"
    }]
  }
}
```

---

## Validation

The mapper automatically validates:
- ✅ Only allowed sections are populated
- ✅ No disallowed sections leak through
- ✅ Raises `ValueError` if scope violated

---

## API Usage

```python
from tools.canonical_mapper import map_to_canonical_model

# Map extracted fields to canonical schema
result = map_to_canonical_model(
    document_type="BankStatement",
    extracted_fields={
        "institutionName": "Chase",
        "currentBalance": 25000
    }
)
```

---

## MCP Server Tool

```python
@mcp.tool()
def map_to_canonical_schema(document_type: str, extracted_fields: dict) -> dict:
    return map_to_canonical_model(document_type, extracted_fields)
```

---

## Testing

Run the complete pipeline test:
```bash
python test_pipeline.py
```

Output saved to:
```
output/pipeline_test/
├── 01_classification.json
├── 02_raw_extraction.md
├── 03_extracted_fields.json
├── 04_canonical_output.json
└── 05_normalized_output.json
```

---

## Troubleshooting

### Issue: Field not mapping
**Check**:
1. Is the `sourceField` name correct?
2. Is the `targetPath` allowed for this document type?
3. Does the extracted field exist in input?

### Issue: Section not appearing
**Check**:
1. Is the section in `DOCUMENT_SCOPE` for this doc type?
2. Are there mapping rules for fields in that section?
3. Do extracted fields have values (not null)?

### Issue: Wrong section populated
**Check**:
1. Document type classification correct?
2. Mapping rules file matches document type?
3. Scoping rules properly defined?

---

**Quick Reference Version**: 1.0  
**Last Updated**: 2026-02-03
