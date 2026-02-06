# 🧪 Testing Guide - Quick Start

## Step-by-Step Testing Workflow

### Step 1: Create a User
**File:** [`test_1_create_user.json`](file:///c:/Users/Gaurav%20Kumar%20Saha/Desktop/Confer/supa-los-storage/test_1_create_user.json)

1. Open http://localhost:8000 in your browser
2. Copy the JSON from `test_1_create_user.json`
3. Paste into the textarea
4. Click "Submit"
5. **IMPORTANT:** Copy the `record_id` from the response - this is your user ID!

**Expected Response:**
```json
{
  "success": true,
  "results": [
    {
      "entity": "user",
      "success": true,
      "version_number": null,
      "is_update": false,
      "record_id": "abc12345-6789-..."  // ← COPY THIS!
    }
  ],
  "errors": [],
  "total_processed": 1,
  "total_errors": 0
}
```

---

### Step 2: Submit Complete Financial Profile
**File:** [`test_2_complete_profile.json`](file:///c:/Users/Gaurav%20Kumar%20Saha/Desktop/Confer/supa-los-storage/test_2_complete_profile.json)

1. Open `test_2_complete_profile.json`
2. Replace **ALL** instances of `"PASTE_USER_ID_HERE"` with the user ID from Step 1
3. Copy the updated JSON
4. Paste into the textarea at http://localhost:8000
5. Click "Submit"

**Expected Response:**
```json
{
  "success": true,
  "results": [
    {
      "entity": "employment",
      "success": true,
      "version_number": 1,  // ← First version
      "is_update": false
    },
    {
      "entity": "income",
      "success": true,
      "version_number": 1,  // ← First version
      "is_update": false
    },
    {
      "entity": "asset",
      "success": true,
      "version_number": 1,  // ← First version
      "is_update": false
    },
    {
      "entity": "liability",
      "success": true,
      "version_number": 1,  // ← First version
      "is_update": false
    }
  ],
  "total_processed": 4
}
```

---

### Step 3: Update Income (Test Versioning)
**File:** [`test_3_update_income.json`](file:///c:/Users/Gaurav%20Kumar%20Saha/Desktop/Confer/supa-los-storage/test_3_update_income.json)

1. Open `test_3_update_income.json`
2. Replace `"PASTE_USER_ID_HERE"` with your user ID
3. Submit the JSON

**Expected Response:**
```json
{
  "success": true,
  "results": [
    {
      "entity": "income",
      "success": true,
      "version_number": 2,  // ← Version incremented!
      "is_update": true     // ← This is an update
    }
  ]
}
```

---

## Verify in Supabase

### Check Current Income
Go to Supabase → Table Editor → `incomes` table

You should see **2 rows** for the salary income:

| id | customer_id | income_type | monthly_amount | version_number | is_current | valid_to |
|----|-------------|-------------|----------------|----------------|------------|----------|
| ... | your-id | salary | 50000 | 1 | **false** | 2024-... |
| ... | your-id | salary | 65000 | 2 | **true** | null |

✅ Version 1: `is_current = false`, `valid_to` has a timestamp
✅ Version 2: `is_current = true`, `valid_to` is null

---

## Quick Test JSONs (Copy & Paste)

### 1️⃣ Create User (Ready to use)
```json
{
  "user": {
    "email": "john.doe@example.com",
    "organization_id": "123e4567-e89b-12d3-a456-426614174000"
  }
}
```

### 2️⃣ Add Income Only (Update customer_id first)
```json
{
  "income": {
    "customer_id": "YOUR_USER_ID_HERE",
    "income_type": "salary",
    "monthly_amount": 50000
  }
}
```

### 3️⃣ Add Asset Only (Update customer_id first)
```json
{
  "asset": {
    "customer_id": "YOUR_USER_ID_HERE",
    "asset_type": "bank_account",
    "asset_value": 100000
  }
}
```

### 4️⃣ Batch Update (Update customer_id first)
```json
{
  "income": {
    "customer_id": "YOUR_USER_ID_HERE",
    "income_type": "salary",
    "monthly_amount": 75000
  },
  "asset": {
    "customer_id": "YOUR_USER_ID_HERE",
    "asset_type": "bank_account",
    "asset_value": 150000
  }
}
```

---

## Verification SQL Queries

Run these in Supabase SQL Editor to verify data:

### Check All Current Data for a User
```sql
SELECT * FROM incomes WHERE customer_id = 'YOUR_USER_ID' AND is_current = true;
SELECT * FROM employments WHERE customer_id = 'YOUR_USER_ID' AND is_current = true;
SELECT * FROM assets WHERE customer_id = 'YOUR_USER_ID' AND is_current = true;
SELECT * FROM liabilities WHERE customer_id = 'YOUR_USER_ID' AND is_current = true;
```

### Check Income History (All Versions)
```sql
SELECT 
  income_type,
  monthly_amount,
  version_number,
  is_current,
  valid_from,
  valid_to
FROM incomes 
WHERE customer_id = 'YOUR_USER_ID'
ORDER BY income_type, version_number;
```

### Verify Only One Current Version Per Entity
```sql
-- This should return 0 rows (no duplicates)
SELECT 
  customer_id,
  income_type,
  COUNT(*) as current_count
FROM incomes
WHERE is_current = true
GROUP BY customer_id, income_type
HAVING COUNT(*) > 1;
```

---

## Common Issues & Solutions

### ❌ Error: "customer_id is required"
**Solution:** Make sure you replaced `PASTE_USER_ID_HERE` with the actual user ID from Step 1

### ❌ Error: "Foreign key constraint violation"
**Solution:** The user ID doesn't exist. Create a user first using `test_1_create_user.json`

### ❌ No version increment
**Solution:** Check that you're using the same `customer_id` and `income_type` (or other logical identity fields)

---

## Test Files Reference

- [`test_1_create_user.json`](file:///c:/Users/Gaurav%20Kumar%20Saha/Desktop/Confer/supa-los-storage/test_1_create_user.json) - Create a new user
- [`test_2_complete_profile.json`](file:///c:/Users/Gaurav%20Kumar%20Saha/Desktop/Confer/supa-los-storage/test_2_complete_profile.json) - Submit all financial data
- [`test_3_update_income.json`](file:///c:/Users/Gaurav%20Kumar%20Saha/Desktop/Confer/supa-los-storage/test_3_update_income.json) - Update income to test versioning
- [`test_data.json`](file:///c:/Users/Gaurav%20Kumar%20Saha/Desktop/Confer/supa-los-storage/test_data.json) - Comprehensive test scenarios

---

## 🎯 Success Criteria

After completing all 3 steps, you should have:

✅ 1 user in the `users` table
✅ 2 income records (version 1 and 2) with only version 2 marked as current
✅ 1 employment record (version 1)
✅ 1 asset record (version 1)
✅ 1 liability record (version 1)
✅ All records properly linked via `customer_id` foreign key
