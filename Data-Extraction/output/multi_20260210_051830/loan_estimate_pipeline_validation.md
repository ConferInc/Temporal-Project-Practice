# Pipeline Validation Report: Loan Estimate

## Document Metadata

- **Document Name:** loan estimate 1 filled.pdf
- **Document Type/Classification:** Loan Estimate
- **Processing Timestamp:** 2026-02-09T23:49:32.888799Z
- **Pipeline Mode:** Multi-document merge (3 pages split into 3 chunks)
- **Auto-Split:** YES (3 chunks)

---

## Classification Results

- **Final Classification Label:** Multi-document merge (Loan Estimate per page)
- **Confidence Score:** 100% (multi-doc), 83%/58%/50% per page
- **Extraction Tool:** multi (merged from 3 separate extractions)

---

## Payload JSON (Extracted Output)

### Summary of Extracted Fields

Total fields extracted: **33 fields**

Key data captured:
- **Borrowers:** "Michael Jones and Mary Stone"
- **Lender:** "Ficus Bank"
- **Loan Officer:** "Joe Smith" (NMLS #12345)
- **Loan Amount:** $211,000
- **Interest Rate:** 4%
- **Loan Term:** 30 years
- **Loan Purpose:** Purchase
- **Mortgage Type:** Conventional
- **Product:** 5 Year Interest Only, 5/3 Adjustable Rate
- **Total Closing Costs:** $8,791
- **Down Payment:** $29,000
- **APR:** 4.617%
- **Rate Lock:** YES (expires 4/16/2013)

### Full Payload JSON (Canonical)

```json
{
  "deal": {
    "parties": [
      {
        "individual": {
          "full_name": "Michael Jones and Mary Stone"
        },
        "party_role": {
          "value": "Borrower"
        }
      },
      {
        "company_name": "Ficus Bank",
        "individual": {
          "full_name": "Joe Smith",
          "nmls_id": "12345"
        },
        "party_role": {
          "value": "Lender"
        }
      }
    ],
    "transaction_information": {
      "loan_purpose": {
        "value": "Purchase"
      },
      "mortgage_type": {
        "value": "Conventional"
      }
    },
    "disclosures_and_closing": {
      "promissory_note": {
        "principal_amount": 211000.0,
        "interest_rate": "4",
        "loan_term_years": 30
      },
      "loan_estimate_h24": {
        "date_issued": "2/15/2013",
        "product_description": "5 Year Interest Only, 5/3 Adjustable Rate",
        "rate_lock_indicator": "YES",
        "rate_lock_expiration_date": "4/16/2013",
        "monthly_principal_interest": 703.33,
        "prepayment_penalty": "NO",
        "total_closing_costs": 8791.0,
        "estimated_cash_to_close": 27791.0,
        "origination_charges": 3110.0,
        "points_percent": "1",
        "points_amount": "2,110",
        "services_cannot_shop": 820.0,
        "services_can_shop": 1921.0,
        "total_loan_costs": 5851.0,
        "prepaid_interest_per_day": "23.44",
        "prepaid_interest_days": "15",
        "down_payment": 29000.0,
        "annual_percentage_rate": "4.617",
        "total_interest_percentage": "81.18",
        "five_year_total_paid": "54,944",
        "five_year_principal_reduction": "0"
      }
    },
    "identifiers": {
      "lender_case_number": "1234567891330172608"
    }
  }
}
```

---

## Relational / Ingestion JSON

### Full Relational JSON

```json
{
  "_metadata": {
    "source": "RelationalTransformer",
    "timestamp": "2026-02-09T23:49:32.888799Z",
    "table_count": 3,
    "total_rows": 3
  },
  "properties": [],
  "applications": [
    {
      "_ref": "application_0",
      "_operation": "upsert",
      "status": "imported",
      "stage": "processing",
      "loan_amount": 211000.0,
      "key_information": {
        "mortgage_type": "Conventional",
        "loan_purpose": "Purchase",
        "promissory_note": {
          "principal_amount": 211000.0,
          "interest_rate": "4",
          "loan_term_years": 30
        },
        "loan_estimate_h24": {
          "date_issued": "2/15/2013",
          "product_description": "5 Year Interest Only, 5/3 Adjustable Rate",
          "rate_lock_indicator": "YES",
          "rate_lock_expiration_date": "4/16/2013",
          "monthly_principal_interest": 703.33,
          "prepayment_penalty": "NO",
          "total_closing_costs": 8791.0,
          "estimated_cash_to_close": 27791.0,
          "origination_charges": 3110.0,
          "points_percent": "1",
          "points_amount": "2,110",
          "services_cannot_shop": 820.0,
          "services_can_shop": 1921.0,
          "total_loan_costs": 5851.0,
          "prepaid_interest_per_day": "23.44",
          "prepaid_interest_days": "15",
          "down_payment": 29000.0,
          "annual_percentage_rate": "4.617",
          "total_interest_percentage": "81.18",
          "five_year_total_paid": "54,944",
          "five_year_principal_reduction": "0"
        },
        "identifiers": {
          "lender_case_number": "1234567891330172608"
        }
      },
      "_primary_customer_ref": "customer_0",
      "loan_product_id": null
    }
  ],
  "customers": [
    {
      "_ref": "customer_0",
      "_operation": "upsert",
      "customer_type": "individual",
      "first_name": "Michael",
      "last_name": "Jones and Mary Stone"
    }
  ],
  "application_customers": [
    {
      "_ref": "app_cust_0",
      "_operation": "insert",
      "_application_ref": "application_0",
      "_customer_ref": "customer_0",
      "role": "Borrower",
      "sequence": 1
    }
  ],
  "employments": [],
  "incomes": [],
  "demographics": [],
  "residences": [],
  "assets": [],
  "liabilities": []
}
```

---

## Missing & Mismatched Fields Analysis

### 1. Missing Property Information

| Field Name | Canonical Path | Expected Type | Payload Value | Issue |
|------------|----------------|---------------|---------------|-------|
| property_address | `deal.collateral.subject_property.address` | string | **MISSING** | Property address not extracted |
| property_value | `deal.collateral.subject_property.valuation.sales_price` | decimal | **MISSING** | Sales price ($211,000 + down payment?) not extracted |
| property_type | `deal.collateral.subject_property.property_type` | string | **MISSING** | Not extracted |

### 2. Missing Borrower Details

| Field Name | Canonical Path | Expected Type | Payload Value | Issue |
|------------|----------------|---------------|---------------|-------|
| borrower_ssn | `deal.parties[0].individual.ssn` | string | **MISSING** | SSN not extracted |
| borrower_address | `deal.parties[0].addresses[0]` | object | **MISSING** | Borrower address not extracted |
| borrower_email | `deal.parties[0].individual.email` | string | **MISSING** | Contact info not extracted |
| borrower_phone | `deal.parties[0].individual.phone` | string | **MISSING** | Contact info not extracted |

### 3. Multiple Borrowers Not Separated

| Field Name | Canonical Path | Expected Type | Payload Value | Issue |
|------------|----------------|---------------|---------------|-------|
| co-borrower | `deal.parties[1]` with role=Borrower | object | **MISSING** | "Mary Stone" merged into single name field |
| first_name | `customers[0].first_name` | string | "Michael" | ✅ Correct |
| last_name | `customers[0].last_name` | string | "Jones and Mary Stone" | ❌ **INCORRECT** - Should be "Jones" only |

**Expected Structure:**
```json
"parties": [
  {"individual": {"full_name": "Michael Jones"}, "party_role": "Borrower"},
  {"individual": {"full_name": "Mary Stone"}, "party_role": "Co-Borrower"}
]
```

### 4. Missing Lender Information in Relational Output

| Canonical Field | Relational Table | Issue |
|-----------------|------------------|-------|
| `deal.parties[1]` (Ficus Bank) | **NO TABLE** | Lender party not transformed to any table |
| Loan officer (Joe Smith, NMLS #12345) | **NO TABLE** | Loan officer info not mapped |

### 5. Missing Property Table Entry

| Issue | Description |
|-------|-------------|
| No `properties` record | Property information not extracted, so no property record created |
| Application missing `_property_ref` | No foreign key link to property |

### 6. Data Type Issues

| Field Name | Canonical Type | Relational Type | Issue |
|------------|----------------|-----------------|-------|
| interest_rate | string: "4" | Should be numeric: 4.0 | Stored as string instead of decimal |
| points_amount | string: "2,110" | Should be numeric: 2110.0 | String with comma instead of numeric |
| prepaid_interest_per_day | string: "23.44" | Should be numeric: 23.44 | String instead of decimal |
| annual_percentage_rate | string: "4.617" | Should be numeric: 4.617 | String instead of decimal |
| five_year_total_paid | string: "54,944" | Should be numeric: 54944.0 | String with comma |

### 7. Overly Nested Data in key_information

| Issue | Description |
|-------|-------------|
| Complex nested JSONB | All loan estimate data dumped into `applications.key_information` |
| Schema has specific fields | Schema has `applications.loan_amount` (✅ used) but also could use normalized fields |
| Query performance | Deep JSONB nesting makes querying harder vs. flat columns |

### 8. Missing Fees Breakdown

| Field Name | Canonical Path | Expected Type | Payload Value | Issue |
|------------|----------------|---------------|---------------|-------|
| itemized_fees | `deal.disclosures_and_closing.fees[]` | array | **MISSING** | Individual fee line items not extracted |
| services_borrower_can_shop | Details | array | Only total ($1,921) captured | Individual services not extracted |
| services_borrower_cannot_shop | Details | array | Only total ($820) captured | Individual services not extracted |

### 9. Missing Dates and Timestamps

| Field Name | Canonical Path | Expected Type | Payload Value | Issue |
|------------|----------------|---------------|---------------|-------|
| application_date | `deal.transaction_information.application_date` | date | **MISSING** | Not extracted from loan estimate |
| closing_date | `deal.disclosures_and_closing.closing_date` | date | **MISSING** | Expected closing date not extracted |

### 10. Missing Cash-to-Close Breakdown

| Field Name | Canonical Path | Expected Type | Payload Value | Issue |
|------------|----------------|---------------|---------------|-------|
| cash_from_borrower | Details | decimal | Only total ($27,791) | Source of funds breakdown missing |
| seller_credits | `deal.transaction_information.seller_credits` | decimal | **MISSING** | Not extracted |
| adjustments | Details | array | **MISSING** | Cash-to-close adjustments not detailed |

---

## Issue, Cause & Fix Summary

### Issue 1: Multiple Borrowers Treated as Single Entity

**Issue:** "Michael Jones and Mary Stone" parsed as one person with last_name="Jones and Mary Stone"

**Root Cause:**
- Name parsing logic splits on first space only
- Doesn't detect " and " connector indicating multiple people
- No logic to create multiple party records from combined names

**Recommended Fix:**
1. Add name-splitting logic in extraction rules:
   ```python
   if " and " in full_name:
       names = full_name.split(" and ")
       for name in names:
           create_party(name.strip())
   ```
2. Update `_split_name()` in transformer to detect multiple borrowers
3. Create separate `customers` and `application_customers` records for each borrower
4. Assign roles: first = "Borrower", subsequent = "Co-Borrower"

---

### Issue 2: Property Information Missing

**Issue:** Subject property address and details not extracted

**Root Cause:**
- Loan Estimate may not prominently display property address on page 1
- Property info may be on pages 2-3 which weren't fully parsed
- Extraction rules may not target property address fields on Loan Estimate form
- Document split into 3 pages may have lost property context

**Recommended Fix:**
1. Review full loan estimate to locate property address section
2. Update extraction rules to target property fields:
   ```yaml
   - source_field: "Property Address"
     target: "deal.collateral.subject_property.address"
   - source_field: "Sale Price"
     target: "deal.collateral.subject_property.valuation.sales_price"
   ```
3. Improve multi-page document merging to capture property info across pages
4. Validate property info completeness in validation stage

---

### Issue 3: Lender Information Not Mapped to Database

**Issue:** Lender party (Ficus Bank, Joe Smith) captured in canonical but lost in relational transformation

**Root Cause:**
- Transformer explicitly skips parties with `role="Lender"` (line 84 of relational_transformer.py)
- No schema tables for lender/organization information
- Loan officer information has no designated storage location

**Recommended Fix:**
1. **Short-term:** Store lender info in `applications.key_information`:
   ```python
   if party_role == "Lender":
       app_row["key_information"]["lender"] = {
           "company": party.get("company_name"),
           "loan_officer": party.get("individual", {}).get("full_name"),
           "nmls_id": party.get("individual", {}).get("nmls_id")
       }
   ```
2. **Long-term:** Add schema tables:
   - `lenders` table (company_name, nmls_id, contact_info)
   - `loan_officers` table (name, nmls_id, lender_id FK)
   - `applications.lender_id` FK
   - `applications.loan_officer_id` FK

---

### Issue 4: Data Types as Strings Instead of Numeric

**Issue:** Numeric values stored as strings: "4", "2,110", "23.44", etc.

**Root Cause:**
- OCR/extraction returns text strings
- Extraction rules don't specify type conversion
- Canonical assembler doesn't normalize data types
- Commas in numbers prevent automatic float conversion

**Recommended Fix:**
1. Add type coercion in extraction rules:
   ```yaml
   - source_field: "Interest Rate"
     target: "deal.disclosures_and_closing.promissory_note.interest_rate"
     type: float
   ```
2. Add number cleaning in canonical assembler:
   ```python
   def clean_numeric(value):
       if isinstance(value, str):
           value = value.replace(',', '').replace('$', '').strip()
           try:
               return float(value)
           except ValueError:
               return value
       return value
   ```
3. Apply to all financial fields automatically

---

### Issue 5: Missing Property Record

**Issue:** No `properties` table entry created, no property FK on application

**Root Cause:**
- Property data not extracted (see Issue #2)
- Transformer only creates property if `collateral.subject_property` exists
- Without property data, no property record can be created

**Recommended Fix:**
1. Fix Issue #2 (extract property information)
2. Ensure property data populates `deal.collateral.subject_property`
3. Transformer will automatically create property record
4. Set `applications._property_ref` to link application to property

---

### Issue 6: Missing Itemized Fees

**Issue:** Only fee totals extracted, not individual line items

**Root Cause:**
- Loan Estimate has complex fee tables (Section C, E, F, G, H)
- Extraction rules may only target summary/total lines
- Table parsing may not capture all rows
- Fee descriptions and amounts need to be paired correctly

**Recommended Fix:**
1. Enhance extraction to capture fee tables:
   ```yaml
   - source_section: "Closing Cost Details - Section C"
     target: "deal.disclosures_and_closing.fees"
     type: array
     extract_table_rows: true
   ```
2. Implement table extraction logic to capture:
   - Fee description
   - Fee amount
   - Fee category (A, B, C, etc.)
   - Who can shop (yes/no)
3. Create fee-specific transformer logic or store in JSONB

---

### Issue 7: Missing Contact Information

**Issue:** Borrower email, phone, address not extracted

**Root Cause:**
- Loan Estimate form may not display borrower contact details
- These fields may be internal to lender's system
- Form focuses on loan terms, not borrower demographics

**Recommended Fix:**
1. Review loan estimate PDF for presence of contact fields
2. If present, add extraction rules
3. If absent, document that Loan Estimate doesn't contain this data
4. Rely on other documents (URLA, application forms) for contact info
5. Add data source metadata to indicate which fields come from which documents

---

### Issue 8: SSN Not Extracted

**Issue:** Borrower SSN missing (flagged as CRITICAL validation error)

**Root Cause:**
- Loan Estimate form does not contain SSN information
- SSN is not a required disclosure on Loan Estimate per TRID regulations
- System validation rules expect SSN from all documents

**Recommended Fix:**
1. Update validation rules to be document-type-aware:
   ```python
   if doc_type == "LoanEstimate":
       # SSN not expected on this form
       skip_validation("deal.parties[0].individual.ssn")
   ```
2. Mark SSN as "not applicable" for Loan Estimate documents
3. Rely on other documents (URLA, W-2, etc.) for SSN capture
4. Add cross-document validation to ensure SSN captured from appropriate source

---

### Issue 9: Dates Not Extracted

**Issue:** Application date, closing date missing

**Root Cause:**
- "Date Issued" captured (2/15/2013) but not mapped to application_date
- Estimated closing date may not be explicitly stated on Loan Estimate
- Date fields not prioritized in extraction rules

**Recommended Fix:**
1. Map "Date Issued" to application date:
   ```python
   if loan_estimate_h24.get("date_issued"):
       app_row["submitted_at"] = _to_iso_date(loan_estimate_h24["date_issued"])
   ```
2. Extract estimated closing date if present:
   ```yaml
   - source_field: "Closing Date" or "Est. Close"
     target: "deal.disclosures_and_closing.estimated_closing_date"
   ```
3. Add to relational transformation

---

### Issue 10: JSONB Complexity in key_information

**Issue:** Large nested structure in `applications.key_information` makes querying difficult

**Root Cause:**
- Transformer uses `key_information` as catch-all for data without specific schema fields
- 20+ loan estimate fields dumped into single JSONB column
- Schema doesn't have dedicated columns for common loan estimate fields

**Recommended Fix:**
1. **Short-term:** Keep as-is (valid approach for complex disclosure data)
2. **Medium-term:** Promote frequently-queried fields to columns:
   - `applications.interest_rate` (decimal)
   - `applications.apr` (decimal)
   - `applications.monthly_payment` (decimal)
   - `applications.total_closing_costs` (decimal)
   - `applications.down_payment` (decimal)
3. **Long-term:** Create dedicated table:
   - `loan_estimates` table with all H-24 fields as columns
   - `applications.loan_estimate_id` FK

---

## Overall Validation Status

### Status: ⚠️ **CONDITIONAL PASS**

### Blocking Issues

**None** - The output is technically valid for database insertion.

### Major Issues (Non-Blocking but Significant)

1. **MAJOR:** Multiple borrowers merged into single record - data loss
2. **MAJOR:** Property information completely missing - no property record
3. **MAJOR:** Lender information lost in transformation
4. **MEDIUM:** Numeric values stored as strings - data type issues
5. **MEDIUM:** Missing itemized fees - only totals captured
6. **MEDIUM:** SSN missing (but acceptable for this document type)

### Summary Notes

**Strengths:**
- ✅ Document correctly identified and classified (Loan Estimate)
- ✅ Multi-page document successfully merged
- ✅ Comprehensive loan terms extracted (33 fields)
- ✅ Core financial data captured (loan amount, interest rate, APR, costs)
- ✅ Relational structure valid and schema-compliant
- ✅ Customer record created and linked to application
- ✅ Disclosure details preserved in key_information

**Weaknesses:**
- ❌ Multiple borrowers not detected/separated
- ❌ Property information missing entirely
- ❌ Lender organization and loan officer info lost
- ❌ Data types inconsistent (strings vs. numerics)
- ❌ Incomplete fee itemization
- ❌ Contact information missing (but may not be on this form)

**Database Insertion Readiness:**
- ✅ **Ready for insertion** - All required FKs present
- ✅ Schema structure valid
- ⚠️ Data completeness ~60% (loan terms good, property/borrower details weak)
- ⚠️ Data quality issues (name parsing, data types)

**Data Quality Score: 7/10**
- Classification: 10/10 ✅
- Extraction completeness: 6/10 ⚠️
- Data accuracy: 7/10 ⚠️
- Transformation fidelity: 6/10 (data loss)
- Schema compliance: 10/10 ✅

**Recommended Priority Fixes:**
1. **HIGH:** Detect and separate multiple borrowers (Issue #1)
2. **HIGH:** Extract property information (Issue #2)
3. **MEDIUM:** Map lender information (Issue #3)
4. **MEDIUM:** Fix data types for numeric fields (Issue #4)
5. **LOW:** Make SSN validation document-type-aware (Issue #8)

---

## Conclusion

The Loan Estimate pipeline demonstrates **strong classification and comprehensive financial data extraction**. The 33 fields captured represent good coverage of loan terms, costs, and disclosures. Multi-page document handling worked correctly.

However, **critical borrower and property information is missing or incorrectly parsed**, and **lender information is lost during transformation**. The output is database-ready but **incomplete for a full loan application workflow**.

**Production Readiness: 70%** - Suitable for capturing loan terms and disclosures, but needs improvement in borrower entity resolution and property data extraction for end-to-end application processing.
