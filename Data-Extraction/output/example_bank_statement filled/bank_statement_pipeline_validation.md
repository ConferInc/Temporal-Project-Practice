# Pipeline Validation Report: Bank Statement

## Document Metadata

- **Document Name:** example_bank_statement filled.pdf
- **Document Type/Classification:** Bank Statement  
- **Processing Timestamp:** 2026-02-09T23:52:03.673051Z
- **Pipeline Mode:** nested
- **Pages:** 2

---

## Classification Results

- **Final Classification Label:** DocumentType.BANK_STATEMENTS
- **Confidence Score:** 95%
- **Extraction Tool:** parse_document_with_dockling

---

## Payload JSON (Extracted Output)

### Summary of Extracted Fields

Total fields extracted: **39 fields**

Key data captured:
- **Account Holder:** ABEL NEWTON
- **Institution:** Bank of America, N.A.
- **Account Number:** 333 4444 5555
- **Account Type:** Adv Plus Banking (Checking)
- **Statement Period:** May 1-31, 2019
- **Beginning Balance:** $25,000
- **Ending Balance:** $25,000
- **Total Deposits:** $200
- **Total Withdrawals:** $200
- **Transactions:** 4 deposits, 4 withdrawals extracted

---

## Missing & Mismatched Fields Analysis

### 1. Duplicate Transactions Data

| Issue | Description |
|-------|-------------|
| **CRITICAL DATA ERROR** | Identical transactions listed in both `transactions` and `withdrawal_transactions` arrays |
| Expected behavior | `transactions` = deposits only, `withdrawal_transactions` = withdrawals only |
| Actual behavior | Both arrays contain same 4 transactions (all labeled as "Deposit" or "Counter credit") |

**Transactions Array (Should be deposits only):**
```json
[
  {"date": "01/05/19", "description": "Deposit", "amount": 50.0},
  {"date": "11/05/19", "description": "Counter credit", "amount": 50.0},
  {"date": "19/05/19", "description": "SEVENELEVENSALARYMAY", "amount": 50.0},
  {"date": "29/05/2019", "description": "Deposit", "amount": 50.0}
]
```

**Withdrawal_Transactions Array (Should be withdrawals only):**
```json
[
  // IDENTICAL to transactions array - this is wrong
  {"date": "01/05/19", "description": "Deposit", "amount": 50.0},
  ...same as above...
]
```

### 2. Missing Withdrawal Transactions

| Field Name | Expected | Payload Value | Issue |
|------------|----------|---------------|-------|
| actual_withdrawals | Array of withdrawal/debit transactions | **MISSING** | Only deposits extracted |
| withdrawal_transaction_count | Numeric count | 0 (implied) | Statement shows $200 total withdrawals but no withdrawal records |

### 3. Missing Customer Contact Information

| Field Name | Canonical Path | Expected Type | Payload Value | Issue |
|------------|----------------|---------------|---------------|-------|
| customer_address | `deal.parties[0].addresses[0]` | object | **MISSING** | Account holder address visible on statement but not extracted |
| customer_phone | `deal.parties[0].individual.phone` | string | **MISSING** | Not extracted |
| customer_email | `deal.parties[0].individual.email` | string | **MISSING** | Not extracted |

### 4. Incomplete Transaction Details

| Field Name | Canonical Path | Expected Type | Payload Value | Issue |
|------------|----------------|---------------|---------------|-------|
| transaction_type | `transactions[].type` | string (debit/credit) | **MISSING** | Type not indicated |
| running_balance | `transactions[].balance_after` | decimal | **MISSING** | Running balance after each transaction not captured |
| check_number | `transactions[].check_number` | string | **MISSING** | If applicable |

### 5. Missing Statement Metadata

| Field Name | Canonical Path | Expected Type | Payload Value | Issue |
|------------|----------------|---------------|---------------|-------|
| statement_date | `assets[0].statement_date` | date | **MISSING** | Date statement was generated |
| page_number | `assets[0].page_info` | string | **MISSING** | "Page 1 of 2" info not captured |

### 6. Data Loss in Relational Transformation

| Canonical Field | Relational Table | Issue |
|-----------------|------------------|-------|
| `assets[0].transactions[]` | **NOT MAPPED** | All transaction details lost |
| `assets[0].withdrawal_transactions[]` | **NOT MAPPED** | All transaction details lost |
| `assets[0].statement_period_start` | **NOT MAPPED** | Period start date lost |
| `assets[0].statement_period_end` | **NOT MAPPED** | Period end date lost |
| `assets[0].beginning_balance` | **NOT MAPPED** | Beginning balance lost |
| `assets[0].ending_balance` | **NOT MAPPED** | Only current value preserved as `cash_or_market_value` |
| `assets[0].total_deposits` | **NOT MAPPED** | Summary amounts lost |
| `assets[0].total_withdrawals` | **NOT MAPPED** | Summary amounts lost |
| `assets[0].account_type` | **NOT MAPPED** | "Adv Plus Banking" lost |

### 7. Date Format Inconsistencies

| Field | Format 1 | Format 2 | Format 3 | Issue |
|-------|----------|----------|----------|-------|
| Transaction dates | "01/05/19" | "29/05/2019" | N/A | Mixed DD/MM/YY and DD/MM/YYYY |
| Statement period | "May l, 2019" (note: "l" instead of "1") | "May 31, 2019" | N/A | OCR error in date + different format |

---

## Issue, Cause & Fix Summary

### Issue 1: Duplicate Transaction Data (CRITICAL)

**Issue:** Same transactions in both deposits and withdrawals arrays

**Root Cause:**
- Extraction rule logic error: both arrays populated from same source
- No distinction made between debit/credit transactions
- Parser may be extracting all transactions twice with different labels
- No transaction type classification applied

**Recommended Fix:**
1. Review extraction rules in `BankStatement.yaml` - likely has:
   ```yaml
   - source: "Deposits"
     target: "assets[0].transactions"
   - source: "Withdrawals"  # BUG: probably maps to same source
     target: "assets[0].withdrawal_transactions"
   ```
2. Implement transaction type detection:
   ```python
   def classify_transaction(description, amount_sign):
       if amount_sign == '+' or 'deposit' in description.lower():
           return 'deposit'
       elif amount_sign == '-' or 'withdrawal' in description.lower():
           return 'withdrawal'
   ```
3. Split transactions correctly into separate arrays

---

### Issue 2: Actual Withdrawals Not Extracted

**Issue:** $200 total withdrawals reported but no withdrawal transaction details captured

**Root Cause:**
- Bank statement likely has separate withdrawal section or uses negative amounts
- Extraction rules don't target withdrawal transaction rows
- May be on page 2 which had less OCR content (229 chars vs 862 on page 1)

**Recommended Fix:**
1. Review full PDF - locate withdrawal transaction section
2. Update extraction rules to target withdrawal table
3. Handle negative amounts: convert to positive with transaction type indicator
4. Ensure both pages fully parsed

---

### Issue 3: Transaction Details Lost in Relational Transformation

**Issue:** Rich transaction history (8 transactions) completely lost in relational output

**Root Cause:**
- No `bank_transactions` table in schema
- `assets` table only stores summary (current value), not transaction history
- Transformer has no logic to map transaction arrays

**Recommended Fix:**
1. **Short-term:** Store transactions in `assets` metadata field (JSONB):
   ```python
   asset_row["metadata"] = {
       "transactions": asset_data.get("transactions", []),
       "statement_period": {
           "start": asset_data.get("statement_period_start"),
           "end": asset_data.get("statement_period_end")
       },
       "beginning_balance": asset_data.get("beginning_balance"),
       "ending_balance": asset_data.get("ending_balance")
   }
   ```
2. **Long-term:** Add schema table:
   ```sql
   CREATE TABLE bank_transactions (
       id uuid PRIMARY KEY,
       asset_id uuid REFERENCES assets(id),
       transaction_date date,
       description text,
       amount numeric,
       transaction_type text, -- 'debit' or 'credit'
       balance_after numeric,
       created_at timestamp
   );
   ```
3. Update transformer to create transaction records

---

### Issue 4: Date Format Inconsistencies and OCR Errors

**Issue:** Mixed date formats and OCR errors ("May l" instead of "May 1")

**Root Cause:**
- OCR misread "1" as "l" (lowercase L)
- Source document has inconsistent date formats
- No normalization applied during extraction

**Recommended Fix:**
1. Add OCR post-processing:
   ```python
   def fix_common_ocr_errors(text):
       # Common number/letter confusions
       text = re.sub(r'\bMay l\b', 'May 1', text)
       text = re.sub(r'\bl(\d)', r'1\1', text)  # "l5" -> "15"
       return text
   ```
2. Normalize all dates to ISO format (YYYY-MM-DD):
   ```python
   dates = ["01/05/19", "29/05/2019", "May 1, 2019"]
   normalized = [normalize_date(d) for d in dates]  
   # All become "2019-05-01", "2019-05-29", "2019-05-01"
   ```

---

### Issue 5: Customer Address Not Extracted

**Issue:** Account holder address visible on bank statement but not captured

**Root Cause:**
- Bank statement address section not targeted by extraction rules
- Address may be in header or footer area
- Focus on transaction data, not account holder demographics

**Recommended Fix:**
1. Add address extraction rule:
   ```yaml
   - source_section: "Account holder address"
     target: "deal.parties[0].addresses[0]"
     extract_multiline: true
   ```
2. Parse address into structured format (street, city, state, zip)
3. Map to `residences` table in relational output

---

### Issue 6: No Transaction Type Indicator in Relational Output

**Issue:** Can't distinguish deposits from withdrawals without transaction type field

**Root Cause:**
- Schema `assets` table doesn't have transaction detail fields
- All transaction data collapsed into single `cash_or_market_value`
- Intended for snapshot, not transaction history

**Recommended Fix:**
1. See Issue #3 fix (add transactions table or store in metadata)
2. If keeping in assets only, use `metadata` JSONB:
   ```json
   "metadata": {
       "transaction_summary": {
           "deposits": 200.0,
           "withdrawals": 200.0,
           "deposit_count": 4,
           "withdrawal_count": 4
       }
   }
   ```

---

### Issue 7: Account Type Not Preserved

**Issue:** "Adv Plus Banking" account type lost in transformation

**Root Cause:**
- Extracted to `assets[0].account_type` in canonical
- Not mapped to `assets.asset_type` in relational (overwritten with generic "Checking")
- Product name vs. account category mismatch

**Recommended Fix:**
1. Store specific product name:
   ```python
   if asset_data.get("account_type"):
       asset_row["description"] = asset_data["account_type"]  
       # "Adv Plus Banking"
   asset_row["asset_type"] = extract_base_type(asset_data.get("account_type"))  
   # "Checking"
   ```
2. Or use metadata:
   ```python
   asset_row.setdefault("metadata", {})["product_name"] = "Adv Plus Banking"
   ```

---

## Overall Validation Status

### Status: ⚠️ **CONDITIONAL PASS with CRITICAL DATA ISSUE**

### Blocking Issues

1. **CRITICAL:** Duplicate transaction data - same transactions in deposits and withdrawals arrays
2. **CRITICAL:** Withdrawal transactions completely missing despite $200 total

### Major Issues (Non-Blocking but Significant)

3. **MAJOR:** Transaction history lost entirely in relational transformation (8 transactions → 0)
4. **MAJOR:** Statement period dates lost
5. **MAJOR:** Beginning/ending balance history lost (only final balance preserved)
6. **MEDIUM:** Customer address not extracted
7. **MEDIUM:** Date format inconsistencies and OCR errors
8. **MEDIUM:** Account type/product name lost

### Summary Notes

**Strengths:**
- ✅ Document correctly classified (Bank Statement, 95% confidence)
- ✅ Core account information extracted (institution, account number, holder name)
- ✅ Account balances captured correctly ($25,000)
- ✅ Customer record properly created and linked
- ✅ Asset record valid and schema-compliant
- ✅ Good field coverage (39 fields)

**Weaknesses:**
- ❌ **CRITICAL:** Transaction data duplication error
- ❌ **CRITICAL:** Missing withdrawal transactions
- ❌ Complete transaction history loss (canonical → relational)
- ❌ Missing customer address
- ❌ Date OCR errors and format inconsistencies
- ❌ Significant data loss during transformation

**Database Insertion Readiness:**
- ✅ **Technically ready** - Schema-compliant structure
- ❌ **Data quality issues** - Duplicate/missing transaction data
- ⚠️ **Data completeness: 40%** - Asset summary OK, transaction details lost
- ⚠️ **Utility for underwriting: LOW** - Can't verify transaction patterns without transaction history

**Data Quality Score: 5/10**
- Classification: 10/10 ✅
- Extraction completeness: 7/10 ⚠️ (got main data but transactions have errors)
- Data accuracy: 3/10 ❌ (duplicate data critical error)
- Transformation fidelity: 3/10 ❌ (massive data loss)
- Schema compliance: 10/10 ✅

**Recommended Priority Fixes:**
1. **CRITICAL:** Fix duplicate transaction extraction (Issue #1)
2. **CRITICAL:** Extract missing withdrawal transactions (Issue #2)
3. **HIGH:** Preserve transaction history in relational output (Issue #3)
4. **MEDIUM:** Fix date OCR errors and normalize formats (Issue #4)
5. **MEDIUM:** Extract customer address (Issue #5)
6. **LOW:** Preserve account type/product name (Issue #7)

---

## Conclusion

The bank statement pipeline achieves good classification and core account data extraction. However, **critical data quality issues exist** with transaction extraction (duplicates, missing withdrawals), and **massive data loss occurs** during canonical→relational transformation (all transaction details discarded).

The output is **technically database-ready but functionally incomplete** for mortgage underwriting purposes. Bank statements are primarily used to:
1. Verify account balances ✅ (works)
2. Review transaction patterns ❌ (data lost)
3. Identify red flags (NSF, large transfers) ❌ (can't analyze without transactions)
4. Verify income deposits ❌ (can't match without transaction details)

**Production Readiness: 40%** - Suitable only for basic account existence verification. **Not suitable for transaction analysis or income verification** until transaction extraction and preservation issues are resolved.

**Immediate Action Required:** Fix transaction extraction logic (critical bug causing duplicates and missing data).
