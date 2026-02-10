# Pipeline Validation Report: Appraisal Report (URAR Form 1004)

## Document Metadata

- **Document Name:** Appraisal_Report_1 FILLED.pdf
- **Document Type/Classification:** Appraisal (Form 1004) / URAR
- **Processing Timestamp:** 2026-02-09T23:58:40.854435Z
- **Pipeline Mode:** Multi-document merge (3 pages, 3 chunks)
- **Auto-Split:** YES (3 pages)
- **Pages:** 3
- **Extraction Tool:** multi (OCR)

---

## Classification Results

- **Final Classification Label:** Appraisal (Form 1004)
- **Confidence Score:** 46% per page, 100% aggregate
- **Extraction Tool:** multi (OCR-based extraction across 3 pages)

---

## Summary

### Extraction Results: **PARTIAL SUCCESS**

**Fields Extracted:** 18 fields
**Data Completeness:** ~30% of expected appraisal data
**Relational Output:** 4 records (property ✅, application ✅, customer ⚠️, junction ✅)

### Key Data Captured:

✅ **Property Information:**
- Address: "76 EWestlandSt, Tucson, AZ 85711"
- County: Pima
- Year Built: 1952
- Living Area: 1,522 sq ft
- Rooms: 7 total, 3 bedrooms, 2 bathrooms
- Lot Size: 12,090 sq ft
- Condition: C3
- Zoning: R-1

✅ **Borrower:** "Philips,Alex" (name parsing issue)
✅ **Lender Case #:** 185675119

---

## Missing & Mismatched Fields Analysis

### 1. Missing Appraised Value (CRITICAL)

| Field Name | Canonical Path | Expected Type | Payload Value | Issue |
|------------|----------------|---------------|---------------|-------|
| **appraised_value** | `collateral.subject_property.valuation.appraised_value` | decimal | **MISSING** | Most important appraisal field missing |
| estimated_market_value | `collateral.subject_property.valuation.sales_price` | decimal | **MISSING** | Property value not captured |

**This is the PRIMARY PURPOSE of an appraisal report!**

### 2. Missing Appraisal Details

| Field Name | Canonical Path | Expected Type | Payload Value | Issue |
|------------|----------------|---------------|---------------|-------|
| appraiser_name | `collateral.subject_property.valuation.appraiser_name` | string | **MISSING** | Who performed appraisal |
| appraisal_date | `collateral.subject_property.valuation.appraisal_date` | date | **MISSING** | When appraisal performed |
| inspection_date | `collateral.subject_property.valuation.inspection_date` | date | **MISSING** | When property inspected |
| appraisal_company | `collateral.subject_property.valuation.appraisal_company` | string | **MISSING** | Company name |

### 3. Name Parsing Failure

| Field | Canonical Value | Relational Value | Issue |
|-------|-----------------|------------------|-------|
| full_name | "Philips,Alex" | "Philips,Alex" | ❌ Not parsed |
| first_name | Should be "Alex" | "Philips,Alex" | ❌ Wrong - full name in first_name |
| last_name | Should be "Philips" | null | ❌ Missing |

### 4. Property Details Missing

| Field Name | Expected Type | Issue |
|------------|---------------|-------|
| property_type | string | Missing (single-family, condo, etc.) |
| construction_type | string | Missing (frame, brick, etc.) |
| foundation_type | string | Missing |
| roof_type | string | Missing |
| heating_type | string | Missing |
| cooling_type | string | Missing |

### 5. Comparable Sales Missing

| Data Element | Issue |
|--------------|-------|
| Comparable #1 | **MISSING** - Address, sale price, adjustments |
| Comparable #2 | **MISSING** |
| Comparable #3 | **MISSING** |
| Adjustment rationale | **MISSING** |

### 6. Missing Valuation Approaches

| Approach | Issue |
|----------|-------|
| Sales Comparison Approach | **MISSING** |
| Cost Approach | **MISSING** |
| Income Approach | **MISSING** (if applicable) |

### 7. Data Type Issues

| Field | Canonical Type | Relational Type | Issue |
|-------|----------------|-----------------|-------|
| bathrooms | string: "2.0" | string: "2.0" | Should be numeric: 2.0 or 2.5 |
| lot_size | string: "12090" | Not mapped | Should be integer: 12090 |

### 8. Address Parsing Issues

| Field | Canonical Value | Relational Value | Issue |
|-------|-----------------|------------------|-------|
| street | "76 EWestlandSt" | "76 EWestlandSt" | ❌ OCR error - should be "76 E Westland St" |
| city | "Tucson" | Not in address JSONB | ⚠️ Lost - only street in address object |
| state | "AZ" | Not in address JSONB | ⚠️ Lost |
| zip | "85711" | Not in address JSONB | ⚠️ Lost |

### 9. Data Loss in Relational Transformation

| Canonical Field | Relational Table | Issue |
|-----------------|------------------|-------|
| city, state, zip | `properties.address` JSONB | Only street preserved, city/state/zip lost |
| county | `properties` | Lost (Pima County not in output) |
| legal_description | `properties` | Lost ("DelMonteVillageLot270") |
| total_room_count | `properties` | Lost (7 rooms) |
| lot_size | `properties` | Lost (12,090 sq ft) |
| condition_rating | `properties` | Lost (C3) |
| zoning | `properties.property_type` | Mapped but incorrect usage (R-1 is zoning, not property type) |

---

## Issue, Cause & Fix Summary

### Issue 1: Missing Appraised Value (CRITICAL)

**Issue:** The most important field in an appraisal - the appraised value - is missing

**Root Cause:**
- Extraction rules don't target the appraised value field
- Form 1004 has value in multiple locations (page 2 typically)
- Multi-page split may have separated value from property context
- OCR may have poor quality on value field area

**Recommended Fix:**
1. Review Form 1004 structure - locate appraised value position
2. Add extraction rule:
   ```yaml
   - source_field: "Indicated Value by Sales Comparison Approach" or "Final Reconciliation"
     target: "deal.collateral.subject_property.valuation.appraised_value"
     type: decimal
   ```
3. Ensure multi-page merging preserves valuation context
4. Add validation rule: FAIL if appraisal document has no appraised_value

---

### Issue 2: Name Not Parsed Correctly

**Issue:** "Philips,Alex" stored as-is instead of parsed into first/last names

**Root Cause:**
- Name has comma format "Last,First" instead of space-separated
- Name parser in transformer only handles space-separated names
- No comma-format detection logic

**Recommended Fix:**
1. Enhance `_split_name()` to detect comma format:
   ```python
   if ',' in full_name:
       parts = full_name.split(',')
       return parts[1].strip(), parts[0].strip()  # First, Last
   ```
2. Handle edge cases (multiple commas, missing spaces)

---

### Issue 3: Comparable Sales Not Extracted

**Issue:** Comparable properties (comps) are core to appraisal methodology but completely missing

**Root Cause:**
- Form 1004 comps section is complex table format
- Extraction rules don't target comp addresses, sale prices, adjustments
- Multi-row table parsing not implemented for comps section

**Recommended Fix:**
1. Add comp extraction to canonical schema:
   ```json
   "comparable_sales": [
     {
       "comp_number": 1,
       "address": "...",
       "sale_price": 250000,
       "sale_date": "2019-03-15",
       "adjustments": {...}
     }
   ]
   ```
2. Implement table parsing for comps grid
3. Create relational mapping (new table or JSONB in properties)

---

### Issue 4: Property Details Lost in Transformation

**Issue:** 6+ property fields extracted but lost during canonical→relational transform

**Root Cause:**
- Transformer's `_transform_property()` doesn't map all fields
- Fields like county, legal_description, lot_size, total_rooms not targeted
- `properties` table doesn't have columns for all these fields
- JSONB `metadata` field available but not utilized

**Recommended Fix:**
1. Use `properties.metadata` JSONB for unmapped fields:
   ```python
   prop_row.setdefault("metadata", {}).update({
       "county": subject.get("county"),
       "legal_description": subject.get("legal_description"),
       "lot_size_sqft": subject.get("lot_size"),
       "total_room_count": subject.get("total_room_count"),
       "condition_rating": subject.get("condition_rating")
   })
   ```
2. Or add columns to properties table for commonly-used fields

---

### Issue 5: Address Components Lost in JSONB

**Issue:** City/state/zip extracted but only street stored in `address` JSONB

**Root Cause:**
- `_parse_address_to_jsonb()` receives pre-parsed components (street, city, state, zip)
- But only `address` field passed to transformer (street only)
- City/state/zip available in canonical but not passed to parser

**Recommended Fix:**
1. Update transformer to use all address components:
   ```python
   if subject.get("address"):
       row["address"] = {
           "street": subject.get("address"),
           "city": subject.get("city"),
           "state": subject.get("state"),
           "zip": subject.get("zip_code")
       }
   ```

---

### Issue 6: OCR Error in Address

**Issue:** "76 EWestlandSt" should be "76 E Westland St"

**Root Cause:**
- OCR concatenated directional prefix "E" with street name
- No space detected between "E" and "Westland"
- No post-processing to fix common OCR street address errors

**Recommended Fix:**
1. Add OCR post-processing for addresses:
   ```python
   def fix_address_ocr(address):
       # Add space after directional prefixes
       address = re.sub(r'(\d+)\s*([NSEW])([A-Z])', r'\1 \2 \3', address)
       return address
   # "76EWestlandSt" -> "76 E WestlandSt"
   ```
2. Apply to all address fields during extraction

---

### Issue 7: Missing Appraiser Information

**Issue:** Appraiser name, company, license # not extracted

**Root Cause:**
- Appraiser signature block typically on page 3
- Extraction rules don't target appraiser credentials section
- May be handwritten signature (harder to OCR)

**Recommended Fix:**
1. Add appraiser extraction rules
2. Store in canonical:
   ```json
   "valuation": {
       "appraiser": {
           "name": "John Smith",
           "company": "ABC Appraisal",
           "license_number": "12345",
           "phone": "555-1234"
       }
   }
   ```
3. Map to `applications.key_information` or create `appraisers` table

---

### Issue 8: Property Type vs. Zoning Confusion

**Issue:** Zoning code "R-1" stored in `property_type` field

**Root Cause:**
- Transformer maps `zoning_classification` to `property_type`
- These are different concepts:
  - Property type = Single Family, Condo, Townhouse
  - Zoning = R-1, C-2, M-1 (municipal zoning codes)

**Recommended Fix:**
1. Don't map zoning to property_type
2. Extract actual property type from form (usually on page 1)
3. Store zoning in `properties.metadata`:
   ```python
   row.setdefault("metadata", {})["zoning"] = subject.get("zoning_classification")
   ```

---

## Overall Validation Status

### Status: ⚠️ **PARTIAL PASS**

### Blocking Issues

1. **CRITICAL:** Appraised value missing - defeats purpose of appraisal
2. **CRITICAL:** No comparable sales data - can't validate appraisal methodology

### Major Issues (Non-Blocking but Significant)

3. **MAJOR:** Appraiser information missing - can't verify who performed appraisal
4. **MAJOR:** Significant data loss in transformation (6+ fields lost)
5. **MEDIUM:** Name parsing failure
6. **MEDIUM:** Address parsing errors (OCR and component loss)
7. **MEDIUM:** Property type incorrectly populated with zoning code

### Summary Notes

**Strengths:**
- ✅ Document correctly classified (Appraisal Form 1004)
- ✅ Property record created ✅
- ✅ Property linked to application ✅
- ✅ Core property details captured (address, size, rooms, year)
- ✅ Multi-page document successfully merged
- ✅ Schema-compliant output

**Weaknesses:**
- ❌ **Appraised value MISSING** - most critical field
- ❌ Comparable sales completely missing
- ❌ Appraiser information missing
- ❌ Significant data loss during transformation
- ❌ Name parsing failure
- ❌ Address OCR errors
- ❌ Property type field incorrectly populated

**Database Insertion Readiness:**
- ✅ **Ready for insertion** - Schema-valid structure
- ❌ **Missing critical data** - Appraised value is required for underwriting
- ⚠️ **Data completeness: 30%** - Property shell good, valuation data missing
- ⚠️ **Utility for underwriting: 20%** - Can't use without appraised value

**Data Quality Score: 4/10**
- Classification: 9/10 ✅
- Extraction completeness: 3/10 ❌ (missing appraised value)
- Data accuracy: 5/10 ⚠️ (OCR errors, parsing issues)
- Transformation fidelity: 4/10 ❌ (data loss)
- Schema compliance: 10/10 ✅

**Recommended Priority Fixes:**
1. **CRITICAL:** Extract appraised value (Issue #1)
2. **HIGH:** Extract comparable sales data (Issue #3)
3. **HIGH:** Fix data loss in transformation (Issue #4)
4. **MEDIUM:** Fix name parsing for comma format (Issue #2)
5. **MEDIUM:** Fix address component preservation (Issue #5)
6. **MEDIUM:** Extract appraiser information (Issue #7)

---

## Conclusion

The appraisal report pipeline demonstrates **successful property data extraction and relational mapping**. The property record is well-structured with good physical characteristic data (size, rooms, year built).

However, **the most critical data element - the appraised value - is completely missing**, along with comparable sales and appraiser information. This makes the output **not suitable for underwriting** despite being technically database-ready.

**Production Readiness: 30%** - Good property data extraction, but missing the core valuation information that is the entire purpose of an appraisal. Must extract appraised value and comparable sales before this can be used in production lending workflows.

The extraction rules need significant enhancement to capture Form 1004's valuation sections (pages 2-3).
