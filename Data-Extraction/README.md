# 📚 Documentation Index

## Canonical Model & Schema Documentation Suite

Welcome to the comprehensive documentation for the **Utility MCP Server's Canonical Model**. This suite provides complete coverage of the canonical schema architecture, mapping system, and data transformation pipeline.

### ✨ **NEW: Automatic Schema Enforcement**

The pipeline now includes **automatic schema enforcement** to ensure all relational payloads are fully compliant with the Supabase database schema. Every document processed produces a complete, database-ready JSON payload with:

- ✅ All required fields guaranteed present
- ✅ Disallowed fields automatically removed  
- ✅ Schema-defined defaults applied
- ✅ Zero manual post-processing needed

**See**: `docs/SCHEMA_ENFORCEMENT.md` | `PIPELINE_UPDATE_SUMMARY.md`

---

## 📖 Documentation Files

### 1. **CANONICAL_MODEL_DOCUMENTATION.md** 
**Main comprehensive documentation**

**Contents**:
- Complete canonical model architecture
- Detailed schema structure (all 10 sections)
- Document-specific mapping system
- Canonical mapper implementation
- Complete pipeline flow with sequence diagrams
- Document scoping rules
- Priority-based field mapping
- List pattern mapping
- Normalization layer
- Real-world examples

**Use this for**: Deep understanding of the entire system

---

### 2. **MAPPING_EXAMPLES.md**
**Real-world mapping scenarios**

**Contents**:
- Bank Statement mapping (with actual test output)
- Pay Stub mapping
- URLA Form mapping (237 rules)
- Government ID mapping
- List pattern mapping deep dive
- Priority-based mapping examples
- Scoping enforcement examples

**Use this for**: Understanding how mapping works in practice

---

### 3. **CANONICAL_QUICK_REFERENCE.md**
**One-page cheat sheet**

**Contents**:
- Schema sections overview table
- Document type scoping rules
- Mapping rule formats
- Priority rules
- Pipeline flow
- Key principles
- File locations
- Common patterns
- API usage
- Troubleshooting guide

**Use this for**: Quick lookups and daily reference

---

### 4. **canonical_schema_diagram.png**
**Visual schema architecture**

**Contents**:
- Visual representation of all 10 canonical sections
- Document type to section mapping arrows
- Color-coded sections
- Legend showing allowed mappings

**Use this for**: Visual understanding of the schema structure

---

## 🗂️ Project Structure Reference

### Core Files
```
UTILITY MCP SERVER/
├── resources/
│   ├── canonical_schema/
│   │   └── schema.json                    # Canonical schema definition
│   └── canonical_mappings/
│       ├── BankStatement.json             # Bank statement mapping rules
│       ├── PayStub.json                   # Pay stub mapping rules
│       ├── URLA.json                      # URLA form mapping rules (237 rules)
│       ├── GovernmentID.json              # Government ID mapping rules
│       └── README.md                      # Mapping rules documentation
│   └── mismo_mapping/
│       └── map_mismo_3_6.json             # MISMO 3.6 Mapping Rules
│
├── tools/
│   ├── canonical_mapper.py                # Core mapping engine (516 lines)
│   ├── mismo_mapper.py                    # MISMO 3.6 XML Generator
│   ├── normalization.py                   # Normalization layer
│   ├── classifier.py                      # Document classifier
│   ├── doctr_tool.py                      # OCR extraction
│   ├── dockling_tool.py                   # Structure-aware parsing
│   ├── structure_extractor.py             # LLM structure extraction
│   ├── unified_extraction.py              # Unified extraction orchestrator
│   └── query.py                           # Document query tool
│
├── orchestrator/
│   └── pipeline_router.py                 # Pipeline routing logic
│
├── server.py                              # FastMCP server
├── test_pipeline.py                       # Complete pipeline test
│
└── output/
    └── pipeline_test/
        ├── 01_classification.json         # Classification output
        ├── 02_raw_extraction.md           # Raw extraction output
        ├── 03_extracted_fields.json       # Structured fields
        ├── 04_canonical_output.json       # Canonical mapping output
        └── 05_normalized_output.json      # Final normalized output
```

---

## 🎯 Quick Start Guide

### Understanding the System

1. **Start with**: `CANONICAL_QUICK_REFERENCE.md` for overview
2. **Deep dive**: `CANONICAL_MODEL_DOCUMENTATION.md` for complete details
3. **See examples**: `MAPPING_EXAMPLES.md` for real scenarios
4. **Visualize**: `canonical_schema_diagram.png` for schema structure

### Running the Pipeline

```bash
# Test the complete pipeline
python test_pipeline.py

# Check output
ls output/pipeline_test/
```

### Using the Canonical Mapper

```python
from tools.canonical_mapper import map_to_canonical_model

# Map extracted fields to canonical schema
result = map_to_canonical_model(
    document_type="BankStatement",
    extracted_fields={
        "institutionName": "Bank of America",
        "currentBalance": 25000,
        "accountNumberMasked": "****5555"
    }
)

# Result: Partial canonical JSON with only transaction & borrower sections
```

---

## 🔑 Key Concepts

### 1. Canonical Schema
A unified, MISMO-compatible schema with 10 main sections that standardizes mortgage document data.

### 2. Document Scoping
Each document type can only populate specific sections of the canonical schema.

Example:
- BankStatement → `transaction`, `borrower`
- PayStub → `financials.incomes`, `employment`
- URLA → All sections

### 3. Priority-Based Mapping
Multiple source fields can map to one target field with fallback priority.

Example:
```json
[
  {"sourceField": "institutionName", "priority": 1},  // Try first
  {"sourceField": "bankName", "priority": 2}          // Fallback
]
```

### 4. List Pattern Mapping
Handles repeating data structures like transaction lists.

Input:
```json
{
  "deposits_1_date": "2024-01-15",
  "deposits_1_amount": 5000,
  "deposits_2_date": "2024-01-22",
  "deposits_2_amount": 3000
}
```

Output:
```json
{
  "transaction": {
    "list": [
      {"date": "2024-01-15", "amount": 5000},
      {"date": "2024-01-22", "amount": 3000}
    ]
  }
}
```

### 5. Deterministic Mapping
NO LLM usage in canonical mapping - pure rule-based logic ensures same input always produces same output.

---

## 📊 Schema Sections Summary

| # | Section | Purpose | Example Documents |
|---|---------|---------|-------------------|
| 1 | **transaction** | Bank account & transactions | Bank Statement |
| 2 | **borrower** | Basic borrower info | Bank Statement, Gov ID |
| 3 | **deal** | Application metadata | URLA |
| 4 | **loan** | Loan details | URLA |
| 5 | **parties** | Detailed party info | URLA, Gov ID |
| 6 | **employment** | Employment history | URLA, Pay Stub |
| 7 | **financials** | Income/Assets/Liabilities | URLA, Pay Stub, Bank Statement |
| 8 | **collateral** | Property information | URLA, Sales Contract |
| 9 | **governmentLoans** | VA/FHA loan details | URLA, VA Forms |
| 10 | **closing** | Closing information | URLA, Closing Disclosure |

---

## 🔄 Pipeline Flow

```
┌─────────────────┐
│  Upload File    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Classifier    │  ← docTR OCR (first 3 pages)
│  (classifier.py)│  ← Keyword/Regex matching
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Extractor     │  ← docTR (OCR) or Dockling (structure-aware)
│ (doctr/dockling)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Structure     │  ← LLM converts to key-value JSON
│   Extractor     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Canonical     │  ← Rule-based mapping (NO LLM)
│     Mapper      │  ← Document scoping
│                 │  ← Priority selection
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Normalization  │  ← Date/currency/enum standardization
│                 │  ← (Future implementation)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Canonical JSON  │  ← Partial schema output
│     Output      │  ← Only relevant sections
└─────────────────┘
```

---

## 🎓 Learning Path

### Beginner
1. Read `CANONICAL_QUICK_REFERENCE.md`
2. View `canonical_schema_diagram.png`
3. Run `python test_pipeline.py`
4. Check output in `output/pipeline_test/`

### Intermediate
1. Read `CANONICAL_MODEL_DOCUMENTATION.md` (sections 1-5)
2. Study `MAPPING_EXAMPLES.md` (Bank Statement example)
3. Review `resources/canonical_mappings/BankStatement.json`
4. Understand `tools/canonical_mapper.py` (main methods)

### Advanced
1. Read complete `CANONICAL_MODEL_DOCUMENTATION.md`
2. Study all examples in `MAPPING_EXAMPLES.md`
3. Review all mapping files in `resources/canonical_mappings/`
4. Deep dive into `tools/canonical_mapper.py` (all 516 lines)
5. Understand scoping enforcement and validation logic

---

## 🛠️ Common Tasks

### Add a New Document Type

1. **Define scope** in `tools/canonical_mapper.py`:
   ```python
   DOCUMENT_SCOPE["NewDocType"] = {"section1", "section2"}
   ```

2. **Create mapping rules** at `resources/canonical_mappings/NewDocType.json`:
   ```json
   [
     {
       "sourceField": "fieldName",
       "targetPath": "section1.field",
       "priority": 1
     }
   ]
   ```

3. **Test**:
   ```python
   result = map_to_canonical_model("NewDocType", extracted_fields)
   ```

### Modify Existing Mapping

1. Edit `resources/canonical_mappings/{DocumentType}.json`
2. Add/modify mapping rules
3. Test with `python test_pipeline.py`

### Debug Mapping Issues

1. Check logs in `logs/` directory
2. Review `output/pipeline_test/03_extracted_fields.json` (LLM output)
3. Review `output/pipeline_test/04_canonical_output.json` (mapping output)
4. Verify scoping rules in `DOCUMENT_SCOPE`
5. Check mapping rules priority

---

## 📈 Statistics

- **Total Schema Sections**: 10
- **Supported Document Types**: 9 (with 10+ defined in classifier)
- **URLA Mapping Rules**: 237
- **Bank Statement Mapping Rules**: 14 (including 2 list patterns)
- **Pay Stub Mapping Rules**: 7
- **Government ID Mapping Rules**: 8
- **Canonical Mapper Lines of Code**: 516
- **Schema Version**: 2.0.0

---

## 🚀 Future Enhancements

1. ✅ **MISMO XML Generation**: Supports MISMO 3.6 XML Generation
2. **Advanced Normalization**: Implement date/currency/enum normalization
3. **Data Dictionary**: Controlled vocabularies and validation rules
4. **Multi-Document Aggregation**: Merge data from multiple documents
5. **Validation Layer**: Business rules and completeness scoring

---

## 📞 Support

### Documentation Issues
If you find errors or need clarification in the documentation:
1. Check `CANONICAL_QUICK_REFERENCE.md` for quick answers
2. Review relevant examples in `MAPPING_EXAMPLES.md`
3. Consult `CANONICAL_MODEL_DOCUMENTATION.md` for detailed explanations

### Code Issues
1. Check logs in `logs/` directory
2. Review test output in `output/pipeline_test/`
3. Verify mapping rules in `resources/canonical_mappings/`
4. Check scoping rules in `tools/canonical_mapper.py`

---

## ✅ Checklist: Understanding the Canonical Model

- [ ] Read `CANONICAL_QUICK_REFERENCE.md`
- [ ] Viewed `canonical_schema_diagram.png`
- [ ] Understand the 10 canonical sections
- [ ] Understand document scoping concept
- [ ] Understand priority-based mapping
- [ ] Understand list pattern mapping
- [ ] Ran `python test_pipeline.py` successfully
- [ ] Reviewed test output files
- [ ] Read at least one complete example in `MAPPING_EXAMPLES.md`
- [ ] Understand the difference between LLM extraction and rule-based mapping
- [ ] Can explain why mapping is deterministic (no LLM)
- [ ] Can explain why output is partial (scoping)
- [ ] Ready to add a new document type mapping

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-03 | Initial documentation suite created |

---

## 🎉 Conclusion

You now have complete documentation for the Canonical Model system:

✅ **Comprehensive Guide**: `CANONICAL_MODEL_DOCUMENTATION.md`  
✅ **Real Examples**: `MAPPING_EXAMPLES.md`  
✅ **Quick Reference**: `CANONICAL_QUICK_REFERENCE.md`  
✅ **Visual Diagram**: `canonical_schema_diagram.png`  
✅ **This Index**: `README_DOCUMENTATION.md`

**Start with the Quick Reference, dive deep with the Main Documentation, and use Examples for practical understanding.**

Happy mapping! 🚀

---

**Documentation Suite Version**: 1.0  
**Last Updated**: 2026-02-03  
**Project**: Utility MCP Server - Mortgage Document Processing
