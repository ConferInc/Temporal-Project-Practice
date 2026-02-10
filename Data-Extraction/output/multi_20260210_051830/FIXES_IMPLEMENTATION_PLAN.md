# Loan Estimate Pipeline Fixes - Implementation Plan

**Document:** loan estimate 1 filled.pdf  
**Date:** 2026-02-10  
**Reference:** loan_estimate_pipeline_validation.md

---

## Executive Summary

The validation report identified **10 major issues** with data completeness and accuracy. This document outlines fixes for the **5 highest-priority, immediately addressable issues**:

1. ✅ **Multiple Borrowers Detection** (HIGH - data loss)
2. ✅ **Lender Information Preservation** (MEDIUM - data loss)  
3. ✅ **Data Type Coercion** (MEDIUM - data quality)
4. ✅ **Date Mapping** (LOW - data completeness)
5. ⚠️ **Property Information** (requires extraction rule updates - documented)

---

## Issue 1: Multiple Borrowers Treated as Single Entity (HIGH)

### Problem
- Input: `"Michael Jones and Mary Stone"`
- Current Output: 1 customer with `last_name: "Jones and Mary Stone"`
- Expected Output: 2 customers (Michael Jones, Mary Stone)

### Root Cause
- Canonical assembler receives combined name as single string
- Name splitting logic doesn't detect " and " conjunction
- No logic to create multiple party records

### Fix Implementation

**File: `src/logic/canonical_assembler.py`**

Add name splitting logic before party assembly:

```python
def _split_multiple_names(full_name: str) -> List[str]:
    """Split 'Name1 and Name2' into separate names."""
    if not full_name:
        return []
    
    # Detect " and " conjunction (common in loan documents)
    if " and " in full_name.lower():
        names = re.split(r'\s+and\s+', full_name, flags=re.IGNORECASE)
        return [n.strip() for n in names if n.strip()]
    
    return [full_name.strip()]

def _process_party_names(party_data: dict) -> List[dict]:
    """Expand party with multiple names into separate parties."""
    individual = party_data.get("individual", {})
    full_name = individual.get("full_name", "")
    
    names = _split_multiple_names(full_name)
    
    if len(names) <= 1:
        return [party_data]  # Single borrower
    
    # Create separate party record for each borrower
    parties = []
    for idx, name in enumerate(names):
        party_copy = copy.deepcopy(party_data)
        party_copy["individual"]["full_name"] = name
        
        # Adjust role for co-borrowers
        if idx > 0 and party_copy.get("party_role", {}).get("value") == "Borrower":
            party_copy["party_role"]["value"] = "Co-Borrower"
        
        parties.append(party_copy)
    
    return parties
```

**Expected Result:**
```json
{
  "parties": [
    {
      "individual": {"full_name": "Michael Jones"},
      "party_role": {"value": "Borrower"}
    },
    {
      "individual": {"full_name": "Mary Stone"},
      "party_role": {"value": "Co-Borrower"}
    }
  ]
}
```

**Relational Output:**
- 2 customer records
- 2 application_customers records (roles: Borrower, Co-Borrower)

---

## Issue 2: Lender Information Lost in Transformation (MEDIUM)

### Problem
- Canonical JSON has lender party: `{"company_name": "Ficus Bank", "individual": {"full_name": "Joe Smith", "nmls_id": "12345"}}`
- Relational transformer skips parties with `role="Lender"`
- Lender information completely lost

### Root Cause
```python
# Line 84 in relational_transformer.py
if role_val == "Lender":
    continue  # ❌ Skips lender party entirely
```

### Fix Implementation

**File: `src/mapping/relational_transformer.py`**

Map lender information to `applications.key_information`:

```python
# In party processing loop, BEFORE the skip:
if role_val == "Lender":
    # Store lender info in application key_information
    lender_info = {
        "lender_name": party.get("company_name"),
        "loan_officer_name": party.get("individual", {}).get("full_name"),
        "loan_officer_nmls": party.get("individual", {}).get("nmls_id"),
    }
    app_row.setdefault("key_information", {})["lender"] = lender_info
    continue  # Still skip for customer creation
```

**Expected Result:**
```json
{
  "applications": [{
    "key_information": {
      "lender": {
        "lender_name": "Ficus Bank",
        "loan_officer_name": "Joe Smith",
        "loan_officer_nmls": "12345"
      }
    }
  }]
}
```

---

## Issue 3: Data Types as Strings Instead of Numeric (MEDIUM)

### Problem
- Numeric values stored as strings: `"4"`, `"2,110"`, `"23.44"`, `"4.617"`, `"54,944"`
- Database expects numeric types for calculations
- Commas prevent automatic conversion

### Root Cause
- OCR/extraction returns text strings
- No type coercion in canonical assembler
- Commas in numbers block float conversion

### Fix Implementation

**File: `src/logic/canonical_assembler.py`**

Add type coercion utility:

```python
def _coerce_numeric(value: Any) -> Union[float, str]:
    """Convert string numbers to float, preserving original if not numeric."""
    if isinstance(value, (int, float)):
        return float(value)
    
    if not isinstance(value, str):
        return value
    
    # Clean and try to convert
    cleaned = value.replace(',', '').replace('$', '').replace('%', '').strip()
    
    try:
        return float(cleaned)
    except ValueError:
        return value  # Return original if not numeric

def _clean_financial_fields(data: dict) -> dict:
    """Apply numeric coercion to known financial fields."""
    financial_fields = [
        "interest_rate", "annual_percentage_rate", "total_interest_percentage",
        "points_percent", "points_amount", "prepaid_interest_per_day",
        "five_year_total_paid", "five_year_principal_reduction",
        "principal_amount", "monthly_principal_interest", "total_closing_costs",
        "estimated_cash_to_close", "origination_charges", "services_cannot_shop",
        "services_can_shop", "total_loan_costs", "down_payment"
    ]
    
    def _coerce_recursive(obj):
        if isinstance(obj, dict):
            return {k: _coerce_numeric(v) if k in financial_fields else _coerce_recursive(v) 
                    for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_coerce_recursive(item) for item in obj]
        return obj
    
    return _coerce_recursive(data)
```

Apply in `assemble()` method before returning canonical JSON.

**Expected Result:**
```json
{
  "promissory_note": {
    "interest_rate": 4.0,  // was "4"
    "principal_amount": 211000.0
  },
  "loan_estimate_h24": {
    "points_amount": 2110.0,  // was "2,110"
    "prepaid_interest_per_day": 23.44,  // was "23.44"
    "annual_percentage_rate": 4.617,  // was "4.617"
    "five_year_total_paid": 54944.0  // was "54,944"
  }
}
```

---

## Issue 4: Date Not Mapped to Application (LOW)

### Problem
- `date_issued: "2/15/2013"` exists in canonical
- Not mapped to `applications.submitted_at`

### Fix Implementation

**File: `src/mapping/relational_transformer.py`**

In `_transform_application()` method:

```python
# After processing loan_estimate_h24
h24 = disclosures.get("loan_estimate_h24")
if h24:
    key_info["loan_estimate_h24"] = h24
    
    # Map date_issued to submitted_at
    if h24.get("date_issued") and "submitted_at" not in row:
        row["submitted_at"] = self._to_iso_date(h24["date_issued"])
```

**Expected Result:**
```json
{
  "applications": [{
    "submitted_at": "2013-02-15",  // Mapped from date_issued
    "key_information": {
      "loan_estimate_h24": {
        "date_issued": "2/15/2013"
      }
    }
  }]
}
```

---

## Issue 5: Property Information Missing (DOCUMENTED)

### Problem
- No property address, value, or type extracted
- Extraction rules don't target property fields

### Analysis
Property information on Loan Estimate forms appears in:
- Section 1: "Property Address"
- Section 2: "Sale Price" or "Appraised Value"

### Required Action (Not Implemented - Needs Document Review)

1. **Review Raw OCR Output** to confirm property fields are present
2. **Add Extraction Rules** (if present):

```yaml
# In LoanEstimate.yaml
- id: property_address
  type: key_value
  key: "Property"
  target_path: "deal.collateral.subject_property.address"

- id: sales_price
  type: regex
  pattern: 'Sale Price[:\s]+\$?([\d,]+(?:\.\d{2})?)'
  group: 1
  target_path: "deal.collateral.subject_property.valuation.sales_price"
  transform: clean_currency
```

3. **Verify** property data flows to `properties` table via existing transformer logic

**Status:** ⚠️ Requires manual review of source document

---

## Implementation Priority

| Priority | Issue | Impact | Effort | Status |
|----------|-------|--------|--------|--------|
| **P0** | Multiple Borrowers | Data Loss | Medium | ✅ Ready |
| **P1** | Lender Information | Data Loss | Low | ✅ Ready |
| **P1** | Data Type Coercion | Data Quality | Low | ✅ Ready |
| **P2** | Date Mapping | Completeness | Low | ✅ Ready |
| **P3** | Property Information | Completeness | High | ⚠️ Needs Review |

---

## Files to Modify

1. ✅ `src/logic/canonical_assembler.py` - Name splitting, type coercion
2. ✅ `src/mapping/relational_transformer.py` - Lender mapping, date mapping
3. ⚠️ `src/rules/LoanEstimate.yaml` - Property extraction (if applicable)

---

## Testing Plan

1. **Re-process** loan estimate document through pipeline
2. **Verify** canonical JSON:
   - 2 separate parties (Michael Jones, Mary Stone)
   - All numeric fields are numbers, not strings
3. **Verify** relational JSON:
   - 2 customer records
   - 2 application_customers records
   - Lender info in applications.key_information.lender
   - applications.submitted_at populated
4. **Compare** before/after field counts

---

## Expected Impact

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Customers Created** | 1 | 2 | +100% |
| **Data Loss** | 3 fields | 0 fields | -100% |
| **Numeric Fields Correct** | 0% | 100% | +100% |
| **Date Fields Populated** | 0 | 1 | +100% |

---

**Status:** Ready for Implementation  
**Estimated Time:** 2-3 hours  
**Risk:** Low (additive changes, no schema modifications)
