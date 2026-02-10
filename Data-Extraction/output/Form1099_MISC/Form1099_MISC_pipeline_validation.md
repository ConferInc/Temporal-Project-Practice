# Pipeline Validation Report: Form1099_MISC

## Document Metadata

- **Document Name:** Form1099_MISC.jpeg
- **Document Type/Classification:** Form 1099-MISC
- **Processing Timestamp:** 2026-02-09T23:45:47.705804Z
- **Pipeline Mode:** nested

---

## Classification Results

- **Final Classification Label:** DocumentType.FORM_1099_MISC
- **Confidence Score:** 95%
- **Extraction Tool:** ocr_document

---

## Payload JSON (Extracted Output)

### Summary of Extracted Fields

Total fields extracted: **9 fields**

Key data captured:
- Business name: "MICHAEL M JORDAN"
- Business address: "STERLING HEIGHTS"
- Business phone: "517-200-9968"
- Rents income: $1450.00
- Royalties income: $3250.00
- Federal tax withheld: $6750.00
- Document type: "1099-MISC"

### Full Payload JSON

```json
{
  "deal": {
    "parties": [
      {
        "self_employment": [
          {
            "business_name": "MICHAEL M JORDAN",
            "business_address_street": "STERLING HEIGHTS",
            "business_phone": "517-200-9968"
          }
        ],
        "addresses": [
          {
            "street": "7 Payer made direct sales",
            "city_state_zip_raw": "8 Substitute payments in lieu"
          }
        ],
        "income": [
          {
            "non_w2_income": {
              "rents": "1450.00",
              "royalties": "3250.00"
            }
          }
        ],
        "taxes": [
          {
            "federal_withheld_amount": "6750.00"
          }
        ],
        "income_documents": [
          {
            "document_type": "1099-MISC"
          }
        ]
      }
    ]
  }
}
```

---

## Canonical JSON (Expected Output)

Same as payload JSON (canonical structure).

---

## Relational / Ingestion JSON

### Full Relational JSON

```json
{
  "_metadata": {
    "source": "RelationalTransformer",
    "timestamp": "2026-02-09T23:45:47.705804Z",
    "table_count": 2,
    "total_rows": 3
  },
  "properties": [],
  "applications": [
    {
      "_ref": "application_0",
      "_operation": "upsert",
      "status": "imported",
      "stage": "processing",
      "loan_product_id": null
    }
  ],
  "customers": [],
  "application_customers": [],
  "employments": [],
  "incomes": [
    {
      "_ref": "income_0_generic_0_rents",
      "_operation": "insert",
      "_customer_ref": "customer_0",
      "_application_ref": "application_0",
      "income_source": "Other",
      "income_type": "Rents",
      "monthly_amount": "1450.00",
      "include_in_qualification": true
    },
    {
      "_ref": "income_0_generic_0_royalties",
      "_operation": "insert",
      "_customer_ref": "customer_0",
      "_application_ref": "application_0",
      "income_source": "Other",
      "income_type": "Royalties",
      "monthly_amount": "3250.00",
      "include_in_qualification": true
    }
  ],
  "demographics": [],
  "residences": [],
  "assets": [],
  "liabilities": []
}
```

---

## Missing & Mismatched Fields Analysis

### 1. Missing Customer Information

| Field Name | Canonical Path | Expected Type | Payload Value | Issue |
|------------|----------------|---------------|---------------|-------|
| recipient_name | `deal.parties[0].individual.full_name` | string | **MISSING** | Not extracted |
| recipient_ssn | `deal.parties[0].individual.ssn` | string | **MISSING** | Not extracted |
| recipient_tin | `deal.parties[0].taxpayer_identification` | string | **MISSING** | Not extracted |

### 2. Missing Payer Information

| Field Name | Canonical Path | Expected Type | Payload Value | Issue |
|------------|----------------|---------------|---------------|-------|
| payer_tin | `deal.parties[0].self_employment[0].business_tin` | string | **MISSING** | Not extracted |
| payer_city | `deal.parties[0].self_employment[0].business_city` | string | **MISSING** | Not extracted from "STERLING HEIGHTS" |
| payer_state | `deal.parties[0].self_employment[0].business_state` | string | **MISSING** | Not extracted |
| payer_zip | `deal.parties[0].self_employment[0].business_zip` | string | **MISSING** | Not extracted |

### 3. Incorrectly Extracted Fields

| Field Name | Canonical Path | Expected Type | Payload Value | Issue |
|------------|----------------|---------------|---------------|-------|
| address | `deal.parties[0].addresses[0].street` | string | "7 Payer made direct sales" | **INCORRECT** - OCR misread form field label as address |
| city_state_zip | `deal.parties[0].addresses[0].city_state_zip_raw` | string | "8 Substitute payments in lieu" | **INCORRECT** - OCR misread form field label |

### 4. Missing Income Fields

| Field Name | Canonical Path | Expected Type | Payload Value | Issue |
|------------|----------------|---------------|---------------|-------|
| other_income | `deal.parties[0].income[0].non_w2_income.other_income` | decimal | **MISSING** | Box 3 value ($1550.00) not captured |
| fishing_boat_proceeds | `deal.parties[0].income[0].non_w2_income.fishing_boat_proceeds` | decimal | **MISSING** | Box 5 not captured |
| medical_health_care | `deal.parties[0].income[0].non_w2_income.medical_health_care` | decimal | **MISSING** | Box 6 not captured |

### 5. Missing Metadata

| Field Name | Canonical Path | Expected Type | Payload Value | Issue |
|------------|----------------|---------------|---------------|-------|
| tax_year | `deal.parties[0].income_documents[0].tax_year` | integer | **MISSING** | Year 2025 visible in raw text but not extracted |
| form_corrected | `deal.parties[0].income_documents[0].corrected` | boolean | **MISSING** | "CORRECTED (if checked)" checkbox not captured |

### 6. Data Loss in Relational Transformation

| Canonical Field | Relational Table | Issue |
|-----------------|------------------|-------|
| `deal.parties[0].self_employment[0]` | **NO TABLE** | Self-employment/payer info not mapped to any table |
| `deal.parties[0].taxes[0].federal_withheld_amount` | **NO TABLE** | Federal tax withheld ($6750.00) lost in transformation |
| `deal.parties[0].income_documents[0]` | `documents` table | Document metadata not mapped |

### 7. Incomplete Customer Record

| Issue | Description |
|-------|-------------|
| Missing `customers` table entry | Customer referenced in incomes (`_customer_ref: "customer_0"`) but no customer record created |
| Missing `application_customers` junction | No link between application and customer |

---

## Issue, Cause & Fix Summary

### Issue 1: Missing Recipient (Customer) Information

**Issue:** Recipient name, SSN/TIN not extracted

**Root Cause:**
- Form 1099-MISC extraction rules focus on payer information (top section)
- Recipient information (middle/bottom section) not targeted by extraction rules
- OCR may have difficulty with the recipient TIN box format

**Recommended Fix:**
1. Update `src/rules/Form1099_MISC.yaml` to add recipient extraction rules:
   ```yaml
   - source_field: "RECIPIENT'S TIN"
     target: "deal.parties[0].individual.ssn"
   - source_field: "RECIPIENT'S name"
     target: "deal.parties[0].individual.full_name"
   ```
2. Add OCR preprocessing for boxed TIN fields
3. Update parser to distinguish payer vs recipient sections

---

### Issue 2: Incorrect Address Extraction

**Issue:** Form field labels extracted as address data

**Root Cause:**
- OCR captured form field labels ("7 Payer made direct sales", "8 Substitute payments in lieu")
- Extraction rules didn't filter out form instructions
- No validation that extracted address looks like a real address

**Recommended Fix:**
1. Add form field label detection and filtering in preprocessing
2. Implement address validation (regex for street patterns, city/state/zip)
3. Update extraction rules to target specific address regions, not generic text
4. Add negative patterns to exclude form instructions

---

### Issue 3: Payer Address Not Properly Parsed

**Issue:** Business address captured as single field "STERLING HEIGHTS" without city/state/zip separation

**Root Cause:**
- Raw OCR text shows "LANSING MI 48310" but extraction captured only "STERLING HEIGHTS"
- Address parsing logic not applied to self-employment business address
- Multi-line address not properly concatenated

**Recommended Fix:**
1. Update relational transformer's `_transform_residence` logic to also handle self-employment addresses
2. Apply `_parse_city_state_zip` helper to business address fields
3. Capture full multi-line payer address in extraction phase

---

### Issue 4: Missing Income Box Values

**Issue:** Only 2 of ~18 possible income boxes extracted (rents and royalties)

**Root Cause:**
- Extraction rules only target commonly-used boxes (1, 2)
- Other income boxes (3, 5, 6, etc.) not included in extraction patterns
- No "scan all numbered boxes" fallback logic

**Recommended Fix:**
1. Update `Form1099_MISC.yaml` to include all 18 income boxes:
   ```yaml
   - source_field: "3 Other income"
     target: "deal.parties[0].income[0].non_w2_income.other_income"
   - source_field: "5 Fishing boat proceeds"
     target: "deal.parties[0].income[0].non_w2_income.fishing_boat_proceeds"
   - source_field: "6 Medical and health care"
     target: "deal.parties[0].income[0].non_w2_income.medical_health_care"
   # ... add remaining boxes
   ```
2. Implement generic box-scanning logic for numbered form fields

---

### Issue 5: Tax Year and Metadata Not Extracted

**Issue:** Year (2025) and corrected checkbox not captured

**Root Cause:**
- Tax year extraction rule not defined
- Checkbox detection not implemented in OCR/extraction pipeline
- Metadata fields not mapped in canonical schema

**Recommended Fix:**
1. Add tax year extraction pattern:
   ```yaml
   - source_field: "For calendar year {YYYY}"
     target: "deal.parties[0].income_documents[0].tax_year"
     pattern: "\\d{4}"
   ```
2. Implement checkbox detection (checked/unchecked) using OCR box analysis
3. Add `corrected` and `tax_year` fields to canonical schema for 1099 documents

---

### Issue 6: Self-Employment Data Lost in Relational Transform

**Issue:** Payer/self-employment information not mapped to any database table

**Root Cause:**
- `relational_transformer.py` doesn't have logic to transform `self_employment` array
- Payer information doesn't fit cleanly into existing tables (not customer, not employment in traditional sense)
- No `payers` or `business_entities` table in schema

**Recommended Fix:**
1. **Short-term:** Store payer info in `application.key_information` JSONB field:
   ```python
   if party.get("self_employment"):
       app_row["key_information"]["payer"] = party["self_employment"]
   ```
2. **Long-term:** Add schema tables:
   - `business_entities` table for payers, employers, etc.
   - `income_sources` table linking incomes to external entities
3. Update transformer to map self-employment to appropriate table

---

### Issue 7: Federal Tax Withheld Not Mapped

**Issue:** $6750.00 federal tax withheld not in relational output

**Root Cause:**
- `deal.parties[0].taxes` array not processed by relational transformer
- No table in schema for tax withholding information
- Tax data typically stored with income or employment records

**Recommended Fix:**
1. Add tax withholding to income records (short-term):
   ```python
   # In _transform_employment or income transformation
   if party.get("taxes"):
       income_row["federal_tax_withheld"] = party["taxes"][0].get("federal_withheld_amount")
   ```
2. Add schema field `incomes.federal_tax_withheld` (optional numeric field)
3. Update canonical model to nest taxes under income records, not as separate array

---

### Issue 8: Missing Customer Record in Relational Output

**Issue:** Income records reference `customer_0` but no customer created

**Root Cause:**
- Canonical JSON has no `individual` object under `parties[0]`
- Transformer only creates customer if `party.individual` exists
- 1099 extraction doesn't populate customer/individual data (recipient info missing)

**Recommended Fix:**
1. Fix Issue #1 first (extract recipient information)
2. Ensure recipient data populates `deal.parties[0].individual`
3. Transformer will then automatically create customer record
4. Alternative: Create stub customer with metadata noting source is 1099 form

---

### Issue 9: Income Amounts May Be Annual, Not Monthly

**Issue:** Income stored as-is, but schema expects `monthly_amount`

**Root Cause:**
- 1099-MISC reports **annual** income
- Transformer doesn't distinguish annual vs monthly income sources
- No conversion logic applied

**Recommended Fix:**
1. Add income frequency metadata to canonical schema:
   ```json
   "income": [{
     "non_w2_income": {
       "rents": "1450.00",
       "frequency": "annual"  // NEW
     }
   }]
   ```
2. Update transformer to convert annual to monthly:
   ```python
   if income_frequency == "annual":
       monthly_amount = annual_amount / 12
   ```
3. Add comment/flag in relational output indicating conversion applied

---

## Overall Validation Status

### Status: ⚠️ **PARTIAL PASS**

### Blocking Issues

1. **CRITICAL:** Missing recipient (customer) information - cannot link income to borrower
2. **CRITICAL:** Incorrect address extraction - form labels captured instead of actual addresses
3. **MAJOR:** Self-employment/payer data lost in relational transformation
4. **MAJOR:** Federal tax withheld data lost ($6750.00)
5. **MAJOR:** Missing customer record but referenced in income records

### Summary Notes

**Strengths:**
- ✅ Document classification accurate (95% confidence)
- ✅ Income values correctly extracted (rents, royalties)
- ✅ Income records properly structured in relational output
- ✅ Schema enforcement working (loan_product_id added)

**Weaknesses:**
- ❌ Only ~40% of form fields extracted (9 out of ~20+ fields)
- ❌ Recipient information completely missing
- ❌ Address parsing failed (form labels extracted)
- ❌ Significant data loss in canonical → relational transformation
- ❌ No customer record created despite being referenced

**Database Insertion Readiness:**
- ⚠️ **Not ready for insertion** - Missing required foreign key (customer_id)
- ⚠️ Income records reference non-existent customer
- ✅ Schema structure is valid
- ⚠️ Data completeness ~40%

**Recommended Priority Fixes:**
1. **HIGH:** Extract recipient name and TIN (Issue #1)
2. **HIGH:** Fix address extraction (Issue #2)
3. **HIGH:** Create customer record or handle missing customer case (Issue #8)
4. **MEDIUM:** Map self-employment data (Issue #6)
5. **MEDIUM:** Map federal tax withheld (Issue #7)
6. **LOW:** Extract remaining income boxes (Issue #4)
7. **LOW:** Extract metadata (year, corrected flag) (Issue #5)

---

## Conclusion

The Form 1099-MISC pipeline demonstrates successful document classification and partial data extraction. However, significant gaps exist in:
- **Completeness:** Only 40% of form fields extracted
- **Accuracy:** Some fields misread (address labels)
- **Transformation:** Data loss during canonical→relational conversion

The output is **not production-ready** for database insertion due to missing customer records and incomplete data. Addressing the high-priority issues would bring this to an acceptable production state.
