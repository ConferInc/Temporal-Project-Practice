# Canonical Mapping Rules

This directory contains document-specific mapping rules for the canonical mapper tool.

## Purpose

These JSON files define how extracted document fields map to the canonical MISMO-compatible schema. Each document type has its own mapping file.

## File Format

Each mapping file is a JSON array of mapping rules:

```json
[
  {
    "sourceField": "fieldNameInExtractedData",
    "targetPath": "path.in.canonical.schema[0].field",
    "default": "optionalDefaultValue"
  }
]
```

### Fields

- **sourceField** (required): The field name in the extracted data
- **targetPath** (required): The path in the canonical schema using dot notation
  - Supports nested objects: `financials.assets`
  - Supports array indexing: `financials.assets[0].institutionName`
- **default** (optional): Default value if sourceField is missing

## Available Mappings

- **BankStatement.json** - Bank statement documents
- **PayStub.json** - Pay stub/paycheck documents
- **URLA.json** - URLA Form 1003 mortgage applications
- **GovernmentID.json** - Government-issued identification documents

## Adding New Document Types

To add a new document type:

1. Create a new JSON file: `{DocumentType}.json`
2. Define mapping rules following the format above
3. Reference the canonical schema at `../canonical_schema/schema.json`
4. Test with the canonical mapper tool

## Example Usage

```python
from tools.canonical_mapper import map_to_canonical_model

result = map_to_canonical_model(
    document_type="BankStatement",  # Matches BankStatement.json
    extracted_fields={
        "bankName": "Chase",
        "endingBalance": 10000
    }
)
```

## Rules

- Mapping is **deterministic** (no LLM usage)
- Missing source fields are **skipped silently**
- Only **populated sections** are included in output
- Target paths must **exist in canonical schema**
- Arrays are **automatically created** as needed

## Canonical Schema Reference

The canonical schema is located at:
`../canonical_schema/schema.json`

Main sections:
- `deal` - Deal-level information
- `loan` - Loan details
- `parties` - Borrowers and co-borrowers
- `employment` - Employment history
- `financials` - Income, assets, liabilities
- `collateral` - Property information
- `governmentLoans` - VA/FHA loan details
- `closing` - Closing information
