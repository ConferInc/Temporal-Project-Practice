# 🔹 ADDITIONAL SYSTEM INSTRUCTION

*(Canonical JSON Standard + Mapping Layer + Batch Ingestion Behavior)*

---

## 1️⃣ Purpose of This Instruction

As part of the versioned Supabase system, you must implement **two mandatory capabilities** and follow a **strict canonical JSON contract**.

These are **not optional**.

This instruction defines:

1. The **standard canonical JSON schema** that will be used for *all ingestion and updates*
2. A **mapping layer** that maps canonical JSON keys to database table columns
3. How the system must handle **first-time ingestion vs partial updates**

---

## 2️⃣ Canonical JSON Is the Source of Truth

You must define, document, and use a **standard canonical JSON format**.

This JSON format is the **official contract** between:

* UI
* Backend
* Database

The canonical JSON format **will not change frequently**.
The database schema **may evolve**, and the mapping layer must absorb those changes.

---

## 3️⃣ Canonical JSON Structure (Required & Guaranteed)

### ✅ Core Rules

* A single payload may contain **one or multiple entities**
* Each entity is identified by a **top-level key**
* The top-level key **explicitly defines the target table**
* The inner object contains fields that map directly to table columns (via mapping layer)

👉 **No field-based inference is required or allowed**

---

### Example: Single-entity payload

```json
{
  "income": {
    "customer_id": "123",
    "income_type": "salary",
    "monthly_amount": 50000
  }
}
```

---

### Example: First-time full submission (multiple entities in ONE JSON)

```json
{
  "employment": {
    "customer_id": "123",
    "employer_name": "Google",
    "employment_type": "full_time"
  },
  "income": {
    "customer_id": "123",
    "income_type": "salary",
    "monthly_amount": 50000
  },
  "asset": {
    "application_id": "app_1",
    "asset_type": "bank_account",
    "asset_value": 100000
  },
  "liability": {
    "application_id": "app_1",
    "liability_type": "loan",
    "monthly_payment": 15000
  }
}
```

This represents **one canonical payload**, containing **multiple entities**, typically used during **first-time ingestion**.

---

### Example: Partial update (later)

```json
{
  "income": {
    "customer_id": "123",
    "income_type": "salary",
    "monthly_amount": 65000
  }
}
```

Only `income` is updated → a **new income version** is created.
Other entities remain unchanged.

---

## 4️⃣ Required Behavior: Batch + Partial Processing

The backend must treat **every payload as a collection of entities**.

### Processing rules:

1. Iterate over **each top-level key**
2. For each entity:

   * Identify target table **from the key**
   * Apply mapping (JSON → DB columns)
   * Apply versioning logic **independently**
3. A single request may result in:

   * Multiple inserts
   * Across multiple tables
   * Each with its own version increment

There is **no assumption** that only one entity exists per request.

---

## 5️⃣ Mandatory Mapping Layer (Very Important)

You must implement a **centralized mapping layer** that maps:

```
canonical JSON keys → database table columns
```

This mapping must be:

* Centralized
* Easy to update
* Independent of business logic
* Used by all ingestion/update paths

---

### Why the Mapping Layer Is Required

* Database schema may evolve
* Column names may change
* Canonical JSON should remain stable
* Updating the DB schema must NOT require changing JSON or UI

---

### Expected Mapping Design

Use a dedicated file, for example:

```
/mappings/entity_column_map.py
```

or

```
/mappings/entity_column_map.json
```

#### Example (conceptual)

```python
ENTITY_COLUMN_MAP = {
  "income": {
    "table": "incomes",
    "columns": {
      "customer_id": "customer_id",
      "income_type": "income_type",
      "monthly_amount": "monthly_amount"
    }
  },
  "employment": {
    "table": "employments",
    "columns": {
      "customer_id": "customer_id",
      "employer_name": "employer_name",
      "employment_type": "employment_type"
    }
  }
}
```

---

### Mapping Usage Rules

* Backend must:

  1. Read the **top-level entity key**
  2. Load mapping for that entity
  3. Map JSON fields → DB columns using the mapping
  4. Apply versioning logic **after mapping**
* No table logic should hardcode column names
* No schema inference based on internal fields

---

## 6️⃣ Explicit Constraints (Non-Negotiable)

You must NOT:

* ❌ Infer table from inner fields
* ❌ Hardcode DB column names in services
* ❌ Mix mapping logic with versioning logic
* ❌ Require JSON changes when DB schema changes
* ❌ Assume only one entity per request

---

## 7️⃣ Mental Model to Follow

> **Canonical JSON is the contract.**
> **Mapping layer is the adapter.**
> **Database schema can evolve independently.**

---

## 8️⃣ Acceptance Criteria

This task is complete only if:

* Canonical JSON schemas are clearly documented
* Multi-entity payloads are supported
* Mapping file exists and is actively used
* Changing a DB column requires only mapping changes
* Versioning works independently per entity
* No business logic depends directly on JSON key names

---

If needed next, you can additionally:

* Define transaction/atomicity rules
* Define per-entity response format
* Add validation or error handling
* Convert this into a formal JSON contract document

---