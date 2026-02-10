# Pipeline Validation Report: URLA (Uniform Residential Loan Application)

---

## 1. Document Metadata

| Attribute | Value |
|-----------|-------|
| **Document Name** | `URLA.pdf` |
| **Document Type** | Uniform Residential Loan Application (Form 1003) |
| **Processing Timestamp** | 2026-02-10 15:08:16 |
| **Extraction Tool** | parse_document_with_dockling |
| **Processing Time** | 114.87s |
| **Engine** | Deterministic Rule Engine (zero LLM) |

---

## 2. Classification Results

| Classification Aspect | Result |
|----------------------|--------|
| **Actual Classification** | DocumentType.UTILITY_BILL |
| **Correct Classification** | DocumentType.URLA (Uniform Residential Loan Application) |
| **Confidence Score** | 90% |
| **Classification Status** | ❌ **INCORRECT** - Critical Error |

**Notes:**
- ❌ Document was **completely misclassified**
- Should be identified as URLA/Form 1003
- Misclassification as UTILITY_BILL caused complete extraction failure
- Wrong extraction rules applied (utility bill rules instead of URLA rules)

---

## 3. Extracted Payload JSON (Canonical Output)

### Summary of Extracted Fields
- **Total Fields:** 4 fields (should be 50+ fields)
- **Data Completeness:** ~1% (99% data loss)
- **Extraction Quality:** FAILED

### Full Canonical JSON

```json
{
  "billing_summary": {
    "invoice_number": "TYPEOFMORTGAGEANDTERMSOFLOAN"
  },
  "service_provider": {
    "mailing_address": {
      "city": "Binghamton",
      "state": "NY",
      "zip_code": "13903"
    }
  }
}
```

**Analysis:**
- ❌ Wrong schema applied (billing_summary, service_provider = utility bill schema)
- ❌ "TYPEOFMORTGAGEANDTERMSOFLOAN" extracted as invoice number (parsing error)
- ❌ Employer city extracted as service provider mailing address
- ✅ City, state, zip correctly identified (but wrong context)

---

## 4. Relational / Ingestion JSON

### Summary
- **Total Tables Populated:** 1 (applications only)
- **Total Rows:** 1
- **Tables with Data:** applications
- **Empty Tables:** customers, employments, incomes, demographics, residences, assets, liabilities

### Full Relational JSON

```json
{
  "_metadata": {
    "source": "RelationalTransformer",
    "timestamp": "2026-02-10T09:40:10.900582Z",
    "table_count": 1,
    "total_rows": 1
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
  "incomes": [],
  "demographics": [],
  "residences": [],
  "assets": [],
  "liabilities": []
}
```

**Analysis:**
- ❌ Only a default application record created
- ❌ No customer data
- ❌ No borrower information
- ❌ No employment data
- ❌ No income data
- ❌ No property data
- ❌ No asset/liability data
- ❌ **100% data loss for all core loan application fields**

---

## 5. Missing & Mismatched Fields Analysis

### Critical Data Available in Document But Not Extracted

#### Section I: Type of Mortgage and Terms of Loan

| Field Name | Location in Document | Expected Type | Payload Value | Status |
|------------|---------------------|---------------|---------------|--------|
| **agency_case_number** | "012-8765111-703" | string | **MISSING** | ❌ **CRITICAL** |
| **lender_case_number** | "112708192" | string | **MISSING** | ❌ **CRITICAL** |
| **loan_type** | "FHA" | string | **MISSING** | ❌ **CRITICAL** |
| **loan_amount** | "$71,186.00" | numeric | **MISSING** | ❌ **CRITICAL** |
| **interest_rate** | "4.25%" | numeric | **MISSING** | ❌ **CRITICAL** |
| **loan_term_months** | "360" | integer | **MISSING** | ❌ **CRITICAL** |
| **amortization_type** | "Fixed Rate" | string | **MISSING** | ❌ **CRITICAL** |

**Impact:** Loan cannot be processed without these core identifiers and terms.

---

#### Section II: Property Information and Purpose of Loan

| Field Name | Location in Document | Expected Type | Payload Value | Status |
|------------|---------------------|---------------|---------------|--------|
| **property_address** | "748 Thompson Island, Milwaukee, WI 53288" | string | **MISSING** | ❌ **CRITICAL** |
| **number_of_units** | "1" | integer | **MISSING** | ❌ **MISSING** |
| **loan_purpose** | "Purchase" | string | **MISSING** | ❌ **CRITICAL** |
| **occupancy_type** | "Primary Residence" | string | **MISSING** | ❌ **CRITICAL** |
| **title_holder_names** | "Samuel Schultz, Jenna Johnson" | string | **MISSING** | ❌ **CRITICAL** |
| **title_holding_manner** | "Joint tenants" | string | **MISSING** | ❌ **MISSING** |
| **estate_type** | "Fee Simple" (checkbox) | string | **MISSING** | ❌ **MISSING** |
| **down_payment_source** | "Checking Savings" | string | **MISSING** | ❌ **MISSING** |

**Impact:** Property details required for collateral evaluation and title work.

---

#### Section III: Borrower Information

| Field Name | Location in Document | Expected Type | Payload Value | Status |
|------------|---------------------|---------------|---------------|--------|
| **borrower_name** | "Samuel Schultz" | string | **MISSING** | ❌ **CRITICAL** |
| **borrower_ssn** | "112-09-0000" | string (masked) | **MISSING** | ❌ **CRITICAL** |
| **borrower_phone** | "607-279-0708" | string | **MISSING** | ❌ **CRITICAL** |
| **borrower_dob** | "03/29/1979" | date | **MISSING** | ❌ **CRITICAL** |
| **years_school** | "14" | integer | **MISSING** | ❌ **MISSING** |
| **marital_status** | "Married" (checkbox) | string | **MISSING** | ❌ **MISSING** |
| **dependents_count** | "0" | integer | **MISSING** | ❌ **MISSING** |
| **present_address** | "4695 Hinkle Deegan Lake Road Syracuse, NY 13224" | string | **MISSING** | ❌ **CRITICAL** |
| **residence_duration** | "0Y6M" | string | **MISSING** | ❌ **MISSING** |
| **former_address** | "8995 Reina Points Willard, WI 54493" | string | **MISSING** | ❌ **MISSING** |
| **former_residence_duration** | "1Y0M" | string | **MISSING** | ❌ **MISSING** |

**Impact:** Cannot create borrower identity, verify credit, or assess stability.

---

#### Section IV: Employment Information

| Field Name | Location in Document | Expected Type | Payload Value | Status |
|------------|---------------------|---------------|---------------|--------|
| **employer_name** | "Thompson-Bartoletti Group" | string | **MISSING** | ❌ **CRITICAL** |
| **employer_address** | "597 Bryon Gardens Apt. 624, Binghamton, NY 13903" | string | **MISSING** | ❌ **CRITICAL** |
| **position_title** | "Warehouse Manager" | string | **MISSING** | ❌ **CRITICAL** |
| **business_phone** | "862-244-1001" | string | **MISSING** | ❌ **MISSING** |
| **years_on_job** | "3Y6M" | string | **MISSING** | ❌ **MISSING** |
| **years_in_profession** | "3" | integer | **MISSING** | ❌ **MISSING** |
| **self_employed** | false (checkbox unchecked) | boolean | **MISSING** | ❌ **MISSING** |

**Impact:** Employment verification and income stability assessment impossible.

---

#### Section V: Monthly Income and Housing Expense

| Field Name | Location in Document | Expected Type | Payload Value | Status |
|------------|---------------------|---------------|---------------|--------|
| **base_employment_income** | "$1,733.00" | numeric | **MISSING** | ❌ **CRITICAL** |
| **overtime_income** | "$580.00" | numeric | **MISSING** | ❌ **CRITICAL** |
| **total_monthly_income** | "$2,313.00" | numeric | **MISSING** | ❌ **CRITICAL** |
| **proposed_first_mortgage** | "$350.19" | numeric | **MISSING** | ❌ **CRITICAL** |
| **hazard_insurance** | "$70.00" | numeric | **MISSING** | ❌ **MISSING** |
| **real_estate_taxes** | "$12.00" | numeric | **MISSING** | ❌ **MISSING** |
| **mortgage_insurance** | "$49.18" | numeric | **MISSING** | ❌ **MISSING** |
| **total_proposed_housing_expense** | "$481.37" | numeric | **MISSING** | ❌ **CRITICAL** |

**Impact:** Cannot calculate DTI (Debt-to-Income) ratio or assess loan affordability.

---

#### Section VI: Assets and Liabilities

| Field Name | Location in Document | Expected Type | Payload Value | Status |
|------------|---------------------|---------------|---------------|--------|
| **cash_deposit** | "$4,000.00" | numeric | **MISSING** | ❌ **CRITICAL** |
| **liability_1_monthly_payment** | "$413.00" | numeric | **MISSING** | ❌ **CRITICAL** |
| **liability_1_months_left** | "48" | integer | **MISSING** | ❌ **MISSING** |
| **liability_1_balance** | "$18,310.00" | numeric | **MISSING** | ❌ **CRITICAL** |
| **liability_2_monthly_payment** | "$139.00" | numeric | **MISSING** | ❌ **CRITICAL** |
| **liability_2_months_left** | "36" | integer | **MISSING** | ❌ **MISSING** |
| **liability_2_balance** | "$4,878.00" | numeric | **MISSING** | ❌ **CRITICAL** |

**Impact:** Cannot verify down payment source or assess total debt obligations.

---

### 5.1 Extraction Completeness Summary

| Data Category | Fields Available | Fields Extracted | Extraction Rate | Status |
|---------------|------------------|------------------|-----------------|--------|
| **Loan Terms** | 7 | 0 | 0% | ❌ **FAIL** |
| **Property Info** | 8 | 0 | 0% | ❌ **FAIL** |
| **Borrower Identity** | 11 | 0 | 0% | ❌ **FAIL** |
| **Employment** | 7 | 0 | 0% | ❌ **FAIL** |
| **Income** | 8 | 0 | 0% | ❌ **FAIL** |
| **Assets** | 1 | 0 | 0% | ❌ **FAIL** |
| **Liabilities** | 6 | 0 | 0% | ❌ **FAIL** |
| **Overall** | 48+ | 0 | 0% | ❌ **FAIL** |

---

### 5.2 Incorrectly Extracted Fields

| Field Name | Canonical Path | Extracted Value | Correct Value | Issue |
|------------|---------------|-----------------|---------------|-------|
| **invoice_number** | `billing_summary.invoice_number` | "TYPEOFMORTGAGEANDTERMSOFLOAN" | N/A (not a utility bill) | Wrong schema applied |
| **service_provider.city** | `service_provider.mailing_address.city` | "Binghamton" | Should be `employer_city` | Wrong context |
| **service_provider.state** | `service_provider.mailing_address.state` | "NY" | Should be `employer_state` | Wrong context |
| **service_provider.zip** | `service_provider.mailing_address.zip_code` | "13903" | Should be `employer_zip` | Wrong context |

---

## 6. Issue, Cause & Fix Summary

### Issue 1: Complete Misclassification (CRITICAL)

**Issue Description:**
- URLA (Form 1003) misclassified as UTILITY_BILL
- Caused 100% extraction failure
- Wrong document schema applied
- Wrong extraction rules used

**Root Cause:**
1. **Classifier Error:** Document classifier failed to recognize URLA form
2. **Pattern Matching:** May have matched on address/city/state patterns common to utility bills
3. **Missing URLA Signatures:** Classifier not trained to recognize Form 1003 headers/structure
4. **Confidence Misleading:** 90% confidence for wrong classification

**Recommended Fix:**

**Priority:** ⚠️ **P0 - CRITICAL**

**1. Add URLA Classification Signatures:**
```python
# In src/logic/classifier.py
URLA_PATTERNS = [
    r"uniform\s+residential\s+loan\s+application",
    r"freddie\s+mac\s+form\s+65",
    r"fannie\s+mae\s+form\s+1003",
    r"type\s+of\s+mortgage\s+and\s+terms\s+of\s+loan",
    r"borrower\s+information",
    r"employment\s+information",
    r"assets\s+and\s+liabilities"
]

# Weight heavily if multiple patterns match
```

**2. Update Classifier Priority:**
```python
# URLA should have higher priority than utility bill
DOCUMENT_PRIORITY = {
    "URLA": 100,
    "UTILITY_BILL": 50
}
```

**3. Add Form Number Detection:**
```python
# Look for "Form 65" or "Form 1003" in first 500 characters
if re.search(r"form\s+(?:65|1003)", text[:500], re.IGNORECASE):
    return DocumentType.URLA
```

---

### Issue 2: No URLA Extraction Rules (BLOCKING)

**Issue Description:**
- No extraction rules exist for URLA document type
- Cannot extract even if correctly classified
- Need comprehensive rule set for all URLA sections

**Root Cause:**
- `src/rules/URLA.yaml` does not exist or is incomplete
- URLA is complex multi-section form requiring extensive regex/key-value rules

**Recommended Fix:**

**Priority:** ⚠️ **P0 - CRITICAL**

**1. Create `src/rules/URLA.yaml`:**

```yaml
document_type: "URLA"
schema_version: "1.0"

rules:
  # Section I: Type of Mortgage and Terms of Loan
  - id: agency_case_number
    type: regex
    pattern: 'Agency Case Number\s+([\d-]+)'
    group: 1
    target_path: "deal.identifiers.agency_case_number"
  
  - id: lender_case_number
    type: regex
    pattern: 'Lender Case\s*Number\s+([\d]+)'
    group: 1
    target_path: "deal.identifiers.lender_case_number"
  
  - id: loan_type
    type: regex
    pattern: 'Applied for:\s*([A-Z]+)'
    group: 1
    target_path: "deal.transaction_information.mortgage_type.value"
  
  - id: loan_amount
    type: regex
    pattern: 'Amount\s+\$?([\d,]+\.\d{2})'
    group: 1
    target_path: "deal.disclosures_and_closing.promissory_note.principal_amount"
    transform: clean_currency
  
  - id: interest_rate
    type: regex
    pattern: 'Interest\s*Rate\s+([\d.]+)\s*%'
    group: 1
    target_path: "deal.disclosures_and_closing.promissory_note.interest_rate"
  
  - id: loan_term
    type: regex
    pattern: 'No\.\s*of\s*Months\s+(\d+)'
    group: 1
    target_path: "deal.disclosures_and_closing.promissory_note.loan_term_months"
  
  # Section II: Property Information
  - id: property_address
    type: regex
    pattern: 'Subject\s*Property\s*Address.*?([0-9]+\s+[A-Za-z\s,]+,\s*[A-Z]{2}\s*\d{5})'
    group: 1
    target_path: "deal.collateral.subject_property.address"
  
  - id: number_of_units
    type: regex
    pattern: 'No\.\s*of\s*Units\s+(\d+)'
    group: 1
    target_path: "deal.collateral.subject_property.number_of_units"
  
  - id: loan_purpose
    type: regex
    pattern: 'Purpose\s*of\s*Loan:\s*(\w+)'
    group: 1
    target_path: "deal.transaction_information.loan_purpose.value"
  
  - id: occupancy_type
    type: regex
    pattern: '\[\s*x\s*\]\s*(Primary|Secondary|Investment)'
    group: 1
    target_path: "deal.collateral.subject_property.occupancy_type.value"
  
  # Section III: Borrower Information
  - id: borrower_name
    type: regex
    pattern: "Borrower's Name.*?\\n\\s*([A-Z][a-z]+\\s+[A-Z][a-z]+)"
    group: 1
    target_path: "deal.parties[0].individual.full_name"
  
  - id: borrower_ssn
    type: regex
    pattern: 'Social Security Number\\s+([\\d-]+)'
    group: 1
    target_path: "deal.parties[0].individual.ssn"
  
  - id: borrower_phone
    type: regex
    pattern: 'Home Phone.*?([\\d-]+)'
    group: 1
    target_path: "deal.parties[0].individual.home_phone"
  
  - id: borrower_dob
    type: regex
    pattern: 'DOB.*?(\\d{2}/\\d{2}/\\d{4})'
    group: 1
    target_path: "deal.parties[0].individual.dob"
  
  # ... Continue for all sections ...
```

**Estimated Effort:** 8-12 hours to create comprehensive URLA extraction rules

---

### Issue 3: No URLA Canonical Strategy (BLOCKING)

**Issue Description:**
- Canonical assembler has no strategy for URLA document type
- Cannot transform flat extraction to canonical structure

**Root Cause:**
- `_STRATEGIES` dict in `canonical_assembler.py` missing URLA entry
- No `_urla_strategy()` method implemented

**Recommended Fix:**

**Priority:** ⚠️ **P0 - CRITICAL**

**Add URLA Strategy to `src/mapping/canonical_assembler.py`:**

```python
def _urla_strategy(self, flat: dict) -> dict:
    """URLA Form 1003: comprehensive loan application."""
    parties = []
    
    # Borrower
    borrower = self._build_party(
        ssn=flat.get("urla_borrower_ssn"),
        full_name=flat.get("urla_borrower_name"),
        dob=flat.get("urla_borrower_dob"),
        role="Borrower",
    )
    
    # Add borrower contact info
    if flat.get("urla_borrower_phone"):
        borrower["individual"]["home_phone"] = flat["urla_borrower_phone"]
    
    # Add borrower addresses
    borrower["addresses"] = []
    if flat.get("urla_present_address"):
        borrower["addresses"].append({
            "street": flat["urla_present_address"],
            "residence_type": "Current",
            "duration": flat.get("urla_present_duration")
        })
    
    # Add borrower employment
    borrower["employment"] = []
    if flat.get("urla_employer_name"):
        borrower["employment"].append({
            "employer_name": flat["urla_employer_name"],
            "position_title": flat.get("urla_position_title"),
            "business_phone": flat.get("urla_business_phone"),
            "years_on_job": flat.get("urla_years_on_job"),
            "monthly_income": {
                "base": flat.get("urla_base_income"),
                "overtime": flat.get("urla_overtime"),
                "total": flat.get("urla_total_income")
            }
        })
    
    parties.append(borrower)
    
    # Co-Borrower (if present)
    if flat.get("urla_coborrower_name"):
        # ... similar logic ...
        pass
    
    result = {"deal": {"parties": parties}}
    
    # Property/Collateral
    if flat.get("urla_property_address"):
        result["deal"]["collateral"] = {
            "subject_property": {
                "address": flat["urla_property_address"],
                "number_of_units": flat.get("urla_number_of_units"),
                "occupancy_type": {"value": flat.get("urla_occupancy_type")}
            }
        }
    
    # Transaction info
    result["deal"]["transaction_information"] = {
        "loan_purpose": {"value": flat.get("urla_loan_purpose")},
        "mortgage_type": {"value": flat.get("urla_loan_type")}
    }
    
    # Disclosures
    result["deal"]["disclosures_and_closing"] = {
        "promissory_note": {
            "principal_amount": flat.get("urla_loan_amount"),
            "interest_rate": flat.get("urla_interest_rate"),
            "loan_term_months": flat.get("urla_loan_term")
        }
    }
    
    # Identifiers
    result["deal"]["identifiers"] = {
        "agency_case_number": flat.get("urla_agency_case_number"),
        "lender_case_number": flat.get("urla_lender_case_number")
    }
    
    return result

# Add to _STRATEGIES dict
_STRATEGIES = {
    # ... existing strategies ...
    "URLA": _urla_strategy,
    "Uniform Residential Loan Application": _urla_strategy,
}
```

**Estimated Effort:** 6-8 hours

---

## 7. Overall Validation Status

### Status: ❌ **FAIL - COMPLETE SYSTEM FAILURE**

### Blocking Issues:
1. ❌ **CRITICAL:** Document completely misclassified (URLA → UTILITY_BILL)
2. ❌ **CRITICAL:** 0% data extraction (all 48+ fields missing)
3. ❌ **BLOCKING:** No URLA extraction rules exist
4. ❌ **BLOCKING:** No URLA canonical strategy exists
5. ❌ **CRITICAL:** No customer/borrower records created
6. ❌ **CRITICAL:** No loan terms captured
7. ❌ **CRITICAL:** No property information captured
8. ❌ **CRITICAL:** Database payload unusable for loan processing

### Summary Notes:

**Classification:**
- ❌ **FAILED** - Wrong document type (90% confidence in wrong answer)
- Classifier needs URLA pattern recognition

**Extraction:**
- ❌ **FAILED** - 0% field extraction rate
- No URLA.yaml extraction rules exist
- Applied wrong rules (utility bill instead of URLA)

**Canonical Assembly:**
- ❌ **FAILED** - Wrong schema structure
- No URLA strategy in canonical assembler
- Extracted billing_summary instead of deal structure

**Relational Transformation:**
- ❌ **FAILED** - No data to transform
- Only default application record created
- All tables empty

**Database Readiness:**
- ❌ **NOT READY** - Completely unusable
- Cannot process loan application
- Cannot verify borrower
- Cannot evaluate property
- Cannot calculate DTI

---

## 8. Data Coverage Statistics

| Metric | Value |
|--------|-------|
| **Expected Fields** | 48+ |
| **Fields Extracted** | 0 |
| **Extraction Rate** | 0% |
| **Data Loss** | 100% |
| **Critical Fields Missing** | 48 |
| **Blocker Issues** | 4 |
| **Classification Accuracy** | 0% (wrong type) |

---

## 9. Recommendations Priority Matrix

| Priority | Issue | Impact | Effort | Blocking |
|----------|-------|--------|--------|----------|
| 🔴 **P0** | Fix URLA classification | CRITICAL | Low (2h) | YES |
| 🔴 **P0** | Create URLA.yaml extraction rules | CRITICAL | High (8-12h) | YES |
| 🔴 **P0** | Implement URLA canonical strategy | CRITICAL | Medium (6-8h) | YES |
| 🟡 **P1** | Add URLA test coverage | HIGH | Medium (4h) | NO |
| 🟡 **P1** | Document URLA field mapping | HIGH | Low (2h) | NO |

**Total Estimated Effort:** 22-28 hours

---

## 10. Root Cause Analysis

### Primary Failure Point: **Classification**

The misclassification of URLA as UTILITY_BILL is the **single point of failure** that caused complete system breakdown.

**Cascade Effect:**
1. Wrong document type identified (URLA → UTILITY_BILL)
2. Wrong extraction rules applied (UtilityBill.yaml instead of URLA.yaml)
3. Wrong canonical strategy used (utility bill schema instead of URLA schema)
4. Wrong data structure generated (billing_summary instead of deal)
5. Wrong fields extracted (invoice_number instead of loan details)
6. Transformation failure (no valid data to transform)
7. Database payload unusable (empty tables)

**Fix Priority:**
Classification fix is **highest priority** as it's the root cause of all downstream failures.

---

## 11. Expected vs. Actual Output Comparison

### What Should Have Been Extracted:

```json
{
  "deal": {
    "parties": [
      {
        "individual": {
          "full_name": "Samuel Schultz",
          "ssn": "112-09-0000",
          "home_phone": "607-279-0708",
          "dob": "03/29/1979"
        },
        "party_role": {"value": "Borrower"},
        "addresses": [
          {
            "street": "4695 Hinkle Deegan Lake Road",
            "city": "Syracuse",
            "state": "NY",
            "zip_code": "13224",
            "residence_type": "Current"
          }
        ],
        "employment": [
          {
            "employer_name": "Thompson-Bartoletti Group",
            "position_title": "Warehouse Manager",
            "business_phone": "862-244-1001",
            "monthly_income": {
              "base": 1733.00,
              "overtime": 580.00,
              "total": 2313.00
            }
          }
        ]
      }
    ],
    "collateral": {
      "subject_property": {
        "address": "748 Thompson Island, Milwaukee, WI 53288",
        "number_of_units": 1,
        "occupancy_type": {"value": "Primary Residence"}
      }
    },
    "transaction_information": {
      "loan_purpose": {"value": "Purchase"},
      "mortgage_type": {"value": "FHA"}
    },
    "disclosures_and_closing": {
      "promissory_note": {
        "principal_amount": 71186.00,
        "interest_rate": 4.25,
        "loan_term_months": 360
      }
    },
    "identifiers": {
      "agency_case_number": "012-8765111-703",
      "lender_case_number": "112708192"
    }
  }
}
```

### What Was Actually Extracted:

```json
{
  "billing_summary": {
    "invoice_number": "TYPEOFMORTGAGEANDTERMSOFLOAN"
  },
  "service_provider": {
    "mailing_address": {
      "city": "Binghamton",
      "state": "NY",
      "zip_code": "13903"
    }
  }
}
```

**Gap:** ~48 critical fields missing

---

## 12. Production Impact Assessment

### If Deployed to Production:

**Borrower Experience:**
- ❌ Loan application rejected/failed
- ❌ Manual data re-entry required
- ❌ Processing delays

**Lender Impact:**
- ❌ Cannot underwrite loan
- ❌ Cannot verify income/employment
- ❌ Cannot process application
- ❌ Regulatory compliance failure

**System Impact:**
- ❌ 100% failure rate for URLA documents
- ❌ Manual processing required
- ❌ Loss of automation value

**Recommendation:** ⛔ **DO NOT DEPLOY** - System completely non-functional for URLA documents

---

**Report Generated:** 2026-02-10  
**Validation Framework Version:** 1.0  
**Document Status:** FAILED - Critical blocking issues prevent any loan processing  
**Next Action:** Implement P0 fixes (classification + extraction rules + canonical strategy)
