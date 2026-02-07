# Claude Agent Instructions

## Project Context
- **Domain**: Mortgage Loan Origination System (LOS) data extraction
- **Goal**: Transform loan documents (PDFs) into MISMO 3.4 XML (industry standard)
- **Business Users**: Loan officers, processors, underwriters (non-technical)
- **Compliance**: Fannie Mae ILAD, GSE requirements

## Architecture Principles
1. **Zero-LLM Extraction**: Deterministic rule-based processing (no AI variability)
2. **Canonical Schema First**: Single source of truth (`schema.json`)
3. **Parallel Processing**: Page-level parallelism (Cloud-native ready)
4. **Rule-Driven**: YAML-based rules (maintainable by business analysts)
5. **Audit-Ready**: Every transformation logged and traceable

## Target Architecture (Vision)
```
Image/PDF → Laundry → Splitter → Classifier → Rule Engine (YAML)
  → Merger (Priority Logic) → Assembler → MISMO XML
```

**Current State** (Phase 1):
- ✅ Classifier, MISMO Mapper, Schema Registry built
- ❌ Laundry, Splitter, Rule Engine, Merger, Assembler still TODO

## Critical Files (DO NOT MODIFY without explicit approval)
- `resources/canonical_schema/schema.json` - Schema definition (315 lines, enum validation)
- `resources/mismo_mapping/map_mismo_3_6.json` - MISMO rules (98 mappings, APPEND ONLY)
- `server.py` - FastMCP API surface (maintain backward compatibility)

## Code Standards

### Python Style
```python
# Always use type hints (Python 3.11+)
def process_document(file_path: str) -> Dict[str, Any]:
    """
    Process a loan document.

    Args:
        file_path: Absolute path to PDF/image file

    Returns:
        Dict containing canonical_data and mismo_xml

    Raises:
        FileNotFoundError: If file doesn't exist
        ValidationError: If data fails schema validation
    """
    pass

# Always use centralized logger
from utils.logging import logger
logger.info(f"Processing {file_path}")

# Always use schema registry (singleton)
from schema_registry import get_schema_registry
schema = get_schema_registry().get_schema()

# Always validate enums
from enum_validator import EnumValidator
validator = EnumValidator(schema)
validator.validate_enum_value("deal.transaction_information.loan_purpose.value", "Purchase", ["Purchase", "Refinance"])
```

### Error Handling
```python
# Use custom exceptions (defined in utils/exceptions.py)
from utils.exceptions import SchemaValidationError, MappingError

# Never swallow exceptions silently
try:
    result = risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}")
    raise MappingError(f"Failed to map canonical data: {e}") from e
```

## Testing Requirements

### File Structure
```
tests/
  data/
    urla_sample.pdf
    w2_sample.pdf
    bank_statement_sample.pdf
  unit/
    test_schema_registry.py
    test_enum_validator.py
    test_classifier.py
  integration/
    test_pipeline_end_to_end.py
```

### Test Patterns
```python
import pytest
from pathlib import Path

def test_classifier_identifies_urla():
    file_path = Path("tests/data/urla_sample.pdf")
    result = classify_document(str(file_path))
    assert result['document_category'] == "URLA (Form 1003)"
    assert result['confidence'] > 0.7

def test_schema_registry_singleton():
    registry1 = get_schema_registry()
    registry2 = get_schema_registry()
    assert registry1 is registry2  # Same instance
```

## Workflow Instructions

### Starting New Work
1. Read `CURRENT_TASK.md` to understand the objective
2. Check `docs/ARCHITECTURE.md` for design context
3. Review existing code patterns (follow existing style)
4. Create feature branch: `git checkout -b feature/<task-name>`

### During Development
- Commit frequently with semantic messages: `"feat: Add Supabase client wrapper"`, `"fix: Handle null SSN in merger"`, `"docs: Update ARCHITECTURE with merger logic"`
- Run tests locally: `pytest tests/`
- Log all major operations: `logger.info()` for flow, `logger.debug()` for details

### Completing Work
1. Update `docs/TASK_LOG.md` with completion date and deliverables
2. Update `docs/ARCHITECTURE.md` if new components added
3. Update `docs/DATA_FLOW.md` if data transformations changed
4. Create pull request with summary
5. Update `CURRENT_TASK.md` for next phase

## Constraints

### Schema Modifications
- ❌ NEVER delete fields from `schema.json`
- ❌ NEVER change enum options without user approval
- ✅ CAN add new optional fields (must default to `null`)
- ✅ CAN add new enum options (must preserve existing)

### Mapping Rules
- ❌ NEVER remove rules from `map_mismo_3_6.json`
- ❌ NEVER change existing XPath mappings (breaks backward compatibility)
- ✅ CAN add new mapping rules (append to end)
- ✅ CAN add comments to rules (document purpose)

### API Compatibility
- ❌ NEVER remove FastMCP tools from `server.py`
- ❌ NEVER change tool signatures (breaks MCP clients)
- ✅ CAN add new tools
- ✅ CAN add optional parameters to existing tools

### Data Integrity
- ❌ NEVER log SSN, DOB, or PII to console/files
- ❌ NEVER modify canonical data after validation (read-only)
- ✅ CAN log anonymized identifiers (loan_id, document type)
- ✅ CAN store PII in Supabase (encrypted at rest)

## Common Patterns

### Enum Validation
```python
# Schema defines enum fields with {value, options} structure
{
    "loan_purpose": {
        "value": null,
        "options": ["Purchase", "Refinance", "Construction", "Other"]
    }
}

# Always validate before setting:
validator = EnumValidator(schema)
validator.validate_enum_value("deal.transaction_information.loan_purpose.value", extracted_value, schema_options)
```

### Array Handling
```python
# Canonical uses Python lists (0-indexed)
canonical_data['deal']['parties'][0]['individual']['first_name'] = "John"

# MISMO uses XPath (1-indexed)
# /MESSAGE/.../PARTY[1]/INDIVIDUAL/NAME/FirstName

# Mapper handles index conversion automatically
```

### Priority Logic (for Phase 3 Merger)
```python
# Document hierarchy (higher = more trusted)
PRIORITY = {
    "W-2 Form": 10,          # IRS verified
    "Tax Return (1040)": 9,  # IRS filed
    "Pay Stub": 7,           # Employer issued
    "Bank Statement": 6,     # Bank verified
    "URLA (Form 1003)": 3,   # Self-reported
}

# When merging, always prefer higher priority source
if priority[doc_type_a] > priority[doc_type_b]:
    merged_value = value_from_doc_a
```

## Resources

### Documentation
- MISMO 3.4 Spec: https://www.mismo.org/standards-and-resources/documentation
- Fannie Mae ILAD: https://singlefamily.fanniemae.com/ilad
- URLA Form 1003: https://www.fanniemae.com/form1003

### Libraries
- `pypdf`: PDF manipulation (splitting, merging)
- `rapidocr-onnxruntime`: OCR for image conversion
- `doctr`: OCR text extraction
- `supabase-py`: Database client
- `pydantic`: Data validation
- `pytest`: Testing framework

### Internal Docs
- `docs/ARCHITECTURE.md` - System design
- `docs/DATA_FLOW.md` - Data transformations
- `docs/TASK_LOG.md` - Phase history
- `CURRENT_TASK.md` - Active work
