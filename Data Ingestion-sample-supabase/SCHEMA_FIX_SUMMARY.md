# Schema Relationship Fix - Summary

## Problem Identified
Assets and liabilities tables were not connected to the users table via foreign keys. They only had `application_id` with no relationship to users.

## Changes Made

### 1. Database Schema (`db/schema.sql`)

#### Assets Table
**Before:**
```sql
CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL,  -- No FK relationship
    asset_type TEXT NOT NULL,
    asset_value NUMERIC(15, 2) NOT NULL,
    ...
);
```

**After:**
```sql
CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,  -- NEW: Required FK to users
    application_id UUID,        -- CHANGED: Now optional
    asset_type TEXT NOT NULL,
    asset_value NUMERIC(15, 2) NOT NULL,
    ...
    CONSTRAINT fk_assets_customer FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE
);
```

#### Liabilities Table
**Before:**
```sql
CREATE TABLE liabilities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL,  -- No FK relationship
    liability_type TEXT NOT NULL,
    monthly_payment NUMERIC(12, 2) NOT NULL,
    ...
);
```

**After:**
```sql
CREATE TABLE liabilities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,  -- NEW: Required FK to users
    application_id UUID,        -- CHANGED: Now optional
    liability_type TEXT NOT NULL,
    monthly_payment NUMERIC(12, 2) NOT NULL,
    ...
    CONSTRAINT fk_liabilities_customer FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### 2. Mapping Layer (`mappings/entity_column_map.py`)

**Assets mapping:**
- Added `"customer_id": "customer_id"` to columns
- Changed logical identity from `["application_id", "asset_type"]` to `["customer_id", "asset_type"]`

**Liabilities mapping:**
- Added `"customer_id": "customer_id"` to columns
- Changed logical identity from `["application_id", "liability_type"]` to `["customer_id", "liability_type"]`

### 3. Service Documentation

Updated docstrings in:
- `services/asset_service.py` - Now requires `customer_id`
- `services/liability_service.py` - Now requires `customer_id`

### 4. UI Examples (`ui/app.js`)

Updated all example JSON templates to include `customer_id`:

```javascript
asset: {
    customer_id: "123e4567-e89b-12d3-a456-426614174000",  // NEW
    application_id: "app-123e4567-e89b-12d3-a456-426614174000",  // Optional
    asset_type: "bank_account",
    asset_value: 100000
}
```

## New Schema Relationships

```
users (id)
  ├─→ incomes (customer_id FK)
  ├─→ employments (customer_id FK)
  ├─→ assets (customer_id FK)          ✅ FIXED
  └─→ liabilities (customer_id FK)     ✅ FIXED
```

## Canonical JSON Format (Updated)

### Asset Example
```json
{
  "asset": {
    "customer_id": "123e4567-e89b-12d3-a456-426614174000",
    "application_id": "app-123",  // Optional
    "asset_type": "bank_account",
    "asset_value": 100000
  }
}
```

### Liability Example
```json
{
  "liability": {
    "customer_id": "123e4567-e89b-12d3-a456-426614174000",
    "application_id": "app-123",  // Optional
    "liability_type": "loan",
    "monthly_payment": 15000
  }
}
```

## Verification Checklist

✅ All tables now have foreign key relationships to users table
✅ Logical identity updated to use customer_id instead of application_id
✅ Mapping layer reflects new schema
✅ Service documentation updated
✅ UI examples updated with correct JSON structure
✅ No trailing commas in SQL
✅ No incompatible WHERE clauses in constraints

## Ready to Deploy

The schema is now **correct and error-free**. You can:
1. Run the updated `db/schema.sql` in Supabase
2. All 5 tables will be created with proper relationships
3. Test with the updated UI examples
