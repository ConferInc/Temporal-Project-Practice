# Pipeline Validation Report: paystubimage

---

## 1. Document Metadata

| Attribute | Value |
|-----------|-------|
| **Document Name** | `paystubimage.pdf` |
| **Document Type** | PAY_STUBS |
| **Processing Timestamp** | 2026-02-10 14:29:23 |
| **Classification Confidence** | 95% |
| **Extraction Tool** | parse_document_with_dockling |
| **Processing Time** | 38.74s |
| **Engine** | Deterministic Rule Engine (zero LLM) |

---

## 2. Classification Results

| Classification Aspect | Result |
|----------------------|--------|
| **Final Classification Label** | DocumentType.PAY_STUBS |
| **Confidence Score** | 95% |
| **Classification Status** | ✅ CORRECT |

**Notes:**
- Document correctly identified as a paystub
- High confidence score indicates clear document structure
- Appropriate extraction tool (Dockling) selected

---

## 3. Extracted Payload JSON (Canonical Output)

### Summary of Extracted Fields
- **Total Fields:** 10
- **Top-Level Sections:** 1 (deal)
- **Parties:** 1
- **Income Verification Fragments:** 1
- **Employment Records:** 1

### Full Canonical JSON

```json
{
  "deal": {
    "parties": [
      {
        "individual": {
          "full_name": "John R. Doe"
        },
        "income_verification_fragments": [
          {
            "current_net_pay": "418.00",
            "ytd_net_pay": "836.00",
            "current_gross_pay": "450.00",
            "ytd_gross_amount": "900.00",
            "pay_period_start": "06/02/06",
            "pay_period_end": "06/16/06",
            "advice_date": "06/19/06",
            "source_doc": {
              "value": "Paystub"
            }
          }
        ],
        "employment": [
          {
            "employment_status": {
              "value": "Current"
            }
          }
        ]
      }
    ]
  }
}
```

---

## 4. Relational / Ingestion JSON

### Summary
- **Total Tables Populated:** 4
- **Total Rows:** 4
- **Tables with Data:** applications (1), customers (1), application_customers (1), employments (1)
- **Empty Tables:** incomes, demographics, residences, assets, liabilities

### Full Relational JSON

```json
{
  "_metadata": {
    "source": "RelationalTransformer",
    "timestamp": "2026-02-10T09:00:01.817754Z",
    "table_count": 4,
    "total_rows": 4
  },
  "properties": [],
  "applications": [
    {
      "_ref": "application_0",
      "_operation": "upsert",
      "status": "imported",
      "stage": "processing",
      "_primary_customer_ref": "customer_0",
      "loan_product_id": null
    }
  ],
  "customers": [
    {
      "_ref": "customer_0",
      "_operation": "upsert",
      "customer_type": "individual",
      "first_name": "John",
      "last_name": "R. Doe"
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
  "employments": [
    {
      "_ref": "employment_0_0",
      "_operation": "insert",
      "_customer_ref": "customer_0",
      "_application_ref": "application_0",
      "employment_type": "W2",
      "is_current": true,
      "start_date": null,
      "employer_name": null
    }
  ],
  "incomes": [],
  "demographics": [],
  "residences": [],
  "assets": [],
  "liabilities": []
}
```

---

## 5. Missing & Mismatched Fields Analysis

### 5.1 Critical Missing Fields (Canonical → Relational)

#### Income Verification Data (COMPLETE DATA LOSS)

| Field Name | Canonical Path | Expected Type | Canonical Value | Relational Value | Status |
|------------|---------------|---------------|-----------------|------------------|--------|
| **current_net_pay** | `deal.parties[0].income_verification_fragments[0].current_net_pay` | string/numeric | "418.00" | ❌ MISSING | **DROPPED** |
| **ytd_net_pay** | `deal.parties[0].income_verification_fragments[0].ytd_net_pay` | string/numeric | "836.00" | ❌ MISSING | **DROPPED** |
| **current_gross_pay** | `deal.parties[0].income_verification_fragments[0].current_gross_pay` | string/numeric | "450.00" | ❌ MISSING | **DROPPED** |
| **ytd_gross_amount** | `deal.parties[0].income_verification_fragments[0].ytd_gross_amount` | string/numeric | "900.00" | ❌ MISSING | **DROPPED** |
| **pay_period_start** | `deal.parties[0].income_verification_fragments[0].pay_period_start` | string (date) | "06/02/06" | ❌ MISSING | **DROPPED** |
| **pay_period_end** | `deal.parties[0].income_verification_fragments[0].pay_period_end` | string (date) | "06/16/06" | ❌ MISSING | **DROPPED** |
| **advice_date** | `deal.parties[0].income_verification_fragments[0].advice_date` | string (date) | "06/19/06" | ❌ MISSING | **DROPPED** |
| **source_doc** | `deal.parties[0].income_verification_fragments[0].source_doc.value` | string | "Paystub" | ❌ MISSING | **DROPPED** |

**Impact:** 
- ❌ All income verification data lost (100% of verification fields)
- ❌ Cannot verify income from paystub
- ❌ Cannot calculate annualized income
- ❌ Cannot verify pay period consistency
- ❌ Critical underwriting data unavailable

---

### 5.2 Incomplete Fields (Present but Null/Empty)

| Field Name | Relational Path | Expected Value | Actual Value | Status |
|------------|----------------|----------------|--------------|--------|
| **employer_name** | `employments[0].employer_name` | "Your Employer" (from raw text) | `null` | ⚠️ **NULL** |
| **start_date** | `employments[0].start_date` | date or null | `null` | ⚠️ **NULL** (schema required) |
| **incomes** | `incomes[]` | Array with income records | `[]` (empty) | ❌ **EMPTY** |

**Impact:**
- Cannot identify employer (employer_name missing from extraction or raw text)
- No income records created despite canonical having income data
- Employment record exists but is largely incomplete

---

### 5.3 Extra or Unexpected Fields

**None identified.** All fields in relational payload are expected based on schema.

---

### 5.4 Type Mismatches

**None identified.** Field types are consistent where data exists.

---

### 5.5 Structural Mismatches

| Canonical Structure | Relational Structure | Issue |
|---------------------|---------------------|-------|
| `income_verification_fragments[]` array (1 record) | No corresponding table/structure | ❌ **Entire array unmapped** |
| Nested income data under party | Flat incomes table (empty) | ❌ **No transformation logic** |

---

## 6. Issue, Cause & Fix Summary

### Issue 1: Income Verification Fragments Data Loss (CRITICAL)

**Issue Description:**
- All 8 fields within `income_verification_fragments[]` are completely absent from relational payload
- This represents 80% of the canonical data extracted from the paystub
- Income amounts, pay periods, YTD totals all lost

**Root Cause:**
1. **No Database Schema:** No tables exist for `pay_periods`, `income_verification`, or similar structures
2. **No Transformation Logic:** `RelationalTransformer._transform()` does not iterate over `party.income_verification_fragments[]`
3. **No Handler Method:** No `_transform_income_verification_fragment()` method exists
4. **Architectural Gap:** Income verification is treated as "extra" data rather than core paystub content

**Code Evidence:**
```python
# RelationalTransformer.transform() - Line ~80-220
# ❌ No code block for:
for fragment in party.get("income_verification_fragments", []):
    # ... transformation logic ...
```

**Recommended Fix:**

**Step 1:** Add database table
```sql
CREATE TABLE pay_periods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id),
    customer_id UUID NOT NULL REFERENCES customers(id),
    employment_id UUID REFERENCES employments(id),
    
    -- Pay period dates
    pay_period_start DATE,
    pay_period_end DATE,
    advice_date DATE,
    
    -- Current period amounts
    current_gross_pay NUMERIC(12,2),
    current_net_pay NUMERIC(12,2),
    
    -- Year-to-date amounts
    ytd_gross_amount NUMERIC(12,2),
    ytd_net_pay NUMERIC(12,2),
    
    -- Metadata
    source_document TEXT,
    verification_data JSONB,  -- For detailed breakdowns
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Step 2:** Add transformation logic to `RelationalTransformer`
```python
# In party loop, after employments (~line 182):

# Income verification fragments (pay periods)
for frag_idx, fragment in enumerate(party.get("income_verification_fragments", [])):
    pay_period_ref = f"pay_period_{idx}_{frag_idx}"
    pay_period_row = {
        "_ref": pay_period_ref,
        "_operation": "insert",
        "_customer_ref": cust_ref,
        "_application_ref": app_ref,
        "_employment_ref": f"employment_{idx}_0" if party.get("employment") else None,
    }
    
    # Pay period dates
    if fragment.get("pay_period_start"):
        pay_period_row["pay_period_start"] = self._to_iso_date(fragment["pay_period_start"])
    if fragment.get("pay_period_end"):
        pay_period_row["pay_period_end"] = self._to_iso_date(fragment["pay_period_end"])
    if fragment.get("advice_date"):
        pay_period_row["advice_date"] = self._to_iso_date(fragment["advice_date"])
    
    # Current period amounts
    if fragment.get("current_gross_pay"):
        pay_period_row["current_gross_pay"] = self._clean_currency(fragment["current_gross_pay"])
    if fragment.get("current_net_pay"):
        pay_period_row["current_net_pay"] = self._clean_currency(fragment["current_net_pay"])
    
    # YTD amounts
    if fragment.get("ytd_gross_amount"):
        pay_period_row["ytd_gross_amount"] = self._clean_currency(fragment["ytd_gross_amount"])
    if fragment.get("ytd_net_pay"):
        pay_period_row["ytd_net_pay"] = self._clean_currency(fragment["ytd_net_pay"])
    
    # Source document
    source = fragment.get("source_doc", {})
    if isinstance(source, dict):
        pay_period_row["source_document"] = source.get("value", "Paystub")
    
    pay_periods.append(pay_period_row)
```

**Step 3:** Add `pay_periods` to result dictionary
```python
# In transform() return statement:
result = {
    # ... existing tables ...
    "pay_periods": pay_periods,  # ADD THIS
    # ... rest of tables ...
}
```

**Priority:** ⚠️ **CRITICAL** - This is core paystub data essential for income verification

**Effort:** Medium (1-2 hours for schema + transformation logic)

---

### Issue 2: Missing Employer Name (QUALITY)

**Issue Description:**
- `employments[0].employer_name` is `null`
- Raw text contains "Your Employer" but extraction may have missed it
- Employment record is incomplete without employer identification

**Root Cause:**
1. **Extraction Issue:** Employer name not captured from raw text into canonical
2. **Generic Label:** "Your Employer" is a placeholder, not actual employer name
3. **Document Quality:** Paystub may be a template/sample without real employer details

**Code Evidence:**
```json
// Canonical JSON - Line 22-28
"employment": [
  {
    "employment_status": {
      "value": "Current"
    }
    // ❌ No employer_name field
  }
]
```

**Recommended Fix:**

**Option 1:** Improve extraction rules
```yaml
# In PayStub.yaml extraction rules:
- id: employer_name
  type: regex
  pattern: '(?:Employer[:]\s*|From[:]\s*)([A-Z][A-Za-z\s&,.]+)'
  group: 1
  target_path: "deal.parties[0].employment[0].employer_name"
```

**Option 2:** Handle generic placeholders
```python
# In _transform_employment():
if emp.get("employer_name"):
    employer = emp["employer_name"]
    # Skip obvious placeholders
    if employer.lower() not in ["your employer", "employer name", "company name"]:
        row["employer_name"] = employer
```

**Option 3:** Make employer_name optional in schema
```python
# In schema_enforcer.py:
"employments": {
    "required": ["customer_id", "application_id", "employment_type", "start_date"],
    # Remove employer_name from required if not always available
    "defaults": {
        "employer_name": None,  # Allow null
    }
}
```

**Priority:** ⚠️ **MEDIUM** - Employer name is important but this may be a document quality issue

**Effort:** Low (30 mins for extraction rule updates)

---

### Issue 3: Empty Incomes Array (CRITICAL)

**Issue Description:**
- `incomes[]` array is completely empty
- Canonical has income data in `income_verification_fragments` but it's not being transformed to incomes
- Expected at least one income record based on gross pay amount

**Root Cause:**
1. **Structural Mismatch:** Income data is in `income_verification_fragments`, not in standard `employment[].monthly_income` structure
2. **No Fallback Logic:** Transformer only looks for `employment[].monthly_income`, doesn't derive income from verification fragments
3. **Design Gap:** Paystub income model differs from W2/employment income model

**Code Evidence:**
```python
# RelationalTransformer - Line ~117-133
# Only processes income from employment.monthly_income
mi = emp.get("monthly_income", {})  # ❌ This is empty in paystub canonical
for inc_type, amount in mi.items():
    # ... creates income records ...
```

**Recommended Fix:**

**Option 1:** Derive monthly income from pay period data
```python
# In party loop, after processing income_verification_fragments:

# If no standard income but we have pay period data, derive income
if not party.get("employment", [{}])[0].get("monthly_income"):
    # Calculate from pay period
    for frag in party.get("income_verification_fragments", []):
        gross = frag.get("current_gross_pay")
        if gross:
            # If biweekly (14-day period), annualize: (gross * 26) / 12
            # This is a heuristic - better to extract pay frequency
            incomes.append({
                "_ref": f"income_{idx}_derived_0",
                "_operation": "insert",
                "_customer_ref": cust_ref,
                "_application_ref": app_ref,
                "income_source": "Employment",
                "income_type": "Base",
                "monthly_amount": float(gross) * 2.166,  # Biweekly to monthly
                "include_in_qualification": True,
                "metadata": {
                    "derived_from": "pay_period",
                    "pay_period_gross": gross,
                    "calculation": "biweekly_to_monthly"
                }
            })
            break  # Only create one derived income record
```

**Option 2:** Link income to pay_periods table
```python
# Don't create income records here - link through pay_periods table
# Income can be queried as: SUM(pay_periods.ytd_gross) / months_in_year
```

**Priority:** ⚠️ **HIGH** - Income records are essential for loan qualification

**Effort:** Low-Medium (1 hour for derivation logic)

---

## 7. Overall Validation Status

### Status: ❌ **FAIL**

### Blocking Issues:
1. ❌ **Income verification data completely lost** (8 critical fields dropped)
2. ❌ **No income records created** (incomes array empty)
3. ⚠️ **Missing employer name** (employment incomplete)

### Summary Notes:

**Extraction Quality:**
- ✅ Classification: Excellent (95% confidence, correct type)
- ✅ Canonical Extraction: Good (10 fields extracted including verification data)
- ✅ Name Parsing: Correct (John R. Doe → John / R. Doe)

**Transformation Quality:**
- ❌ Data Loss: **Critical** (80% of canonical data dropped)
- ❌ Income Verification: Not transformed
- ❌ Income Records: Not created
- ⚠️ Employment: Incomplete (missing employer name)

**Database Readiness:**
- ❌ **NOT READY FOR INGESTION**
- Missing critical income verification data
- Employment records incomplete
- Cannot perform income verification or underwriting

**Recommended Actions:**
1. **IMMEDIATE:** Implement pay_periods table and transformation logic (Issue 1)
2. **HIGH:** Add income derivation from pay periods (Issue 3)
3. **MEDIUM:** Improve employer name extraction (Issue 2)

**Expected Improvement After Fixes:**
- Data Loss: 80% → 0%
- Income Records: 0 → 1+
- Verification Data: 0 fields → 8 fields
- Ingestion Status: NOT READY → READY

---

## 8. Data Coverage Statistics

| Metric | Value |
|--------|-------|
| **Canonical Fields Extracted** | 10 |
| **Relational Fields Populated** | 6 |
| **Fields Dropped** | 8 (80% data loss) |
| **Empty Arrays** | 5 (incomes, demographics, residences, assets, liabilities) |
| **Null Required Fields** | 2 (employer_name, start_date) |
| **Transformation Completeness** | 20% |

---

## 9. Recommendations Priority Matrix

| Priority | Issue | Impact | Effort | Status |
|----------|-------|--------|--------|--------|
| 🔴 **P0** | Income verification fragments not transformed | CRITICAL | Medium | ❌ Open |
| 🟡 **P1** | Empty incomes array | HIGH | Low-Medium | ❌ Open |
| 🟡 **P2** | Missing employer name | MEDIUM | Low | ❌ Open |

---

**Report Generated:** 2026-02-10  
**Validation Framework Version:** 1.0  
**Document Status:** Failed validation - requires fixes before production use
