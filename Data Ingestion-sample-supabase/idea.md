# 🔹 ANTI-GRAVITY SYSTEM INSTRUCTION

*(Versioned Canonical Financial Data Platform on Supabase)*

---

## 1️⃣ What Is Being Built (High-Level Explanation)

You are building a **versioned canonical data platform** for financial and mortgage-related information using **Supabase (Postgres)** as the primary datastore.

This system is designed to store **facts about users and their financial state over time**, not just their latest state.

Examples:

* A user’s income in 2020
* The same user’s updated income in 2023
* A user’s employment history changing over time
* Assets, liabilities, residences, and related data evolving across years

The system must **preserve all historical versions** and **never overwrite past data**.

Think of this system as:

> **“A timeline of financial facts per user, stored in a structured and queryable way.”**

---

## 2️⃣ Core Philosophy (Must Be Understood First)

### ❌ This is NOT a CRUD app

### ✅ This IS a temporal, versioned data system

In this system:

* Data is **append-only**
* “Update” means **new version**, not overwrite
* Every row represents a **fact valid during a time window**

This design supports:

* Auditability
* Time-based reasoning
* Deterministic LLM and MCP usage
* Future compliance requirements

---

## 3️⃣ What I (the User) Will Provide

You (Antigravity) should assume the following inputs are **already handled upstream**:

### I will provide:

* Canonical JSON objects
* Each JSON already matches a target table
* Each JSON already contains identifiers such as:

  * `user_id`
  * `customer_id`
  * `application_id` (when applicable)
* Clean, validated business fields (e.g. income amount, employer name)



You are strictly responsible for **storing canonical data correctly**.

---

## 4️⃣ What the System Must Do (Behavior)

For **every mutable entity** (income, employment, asset, liability, etc.):

1. Detect whether this is:

   * A first-time insert
   * Or an update to an existing logical entity
2. Apply **row-level versioning**
3. Ensure only one version is marked as current
4. Preserve all historical versions forever

---

## 5️⃣ Phase 1 — Database Schema Creation (Mandatory First Step)

Before writing any ingestion logic or UI code, **create the Supabase schema**.

### Schema Design Rules

* Keep schemas **minimal** (2–4 business columns)
* Add **standard versioning columns** to all mutable tables
* Prefer clarity over completeness

---

### Tables to Create (Minimal, Structural Replica)

#### A. users

Represents system users / customers.

```
id (uuid, pk)
organization_id (uuid)
email (text)

version_number (int)
is_current (boolean)
valid_from (timestamp)
valid_to (timestamp)
```

---

#### B. incomes

Stores user income information over time.

```
id (uuid, pk)
customer_id (uuid)
income_type (text)
monthly_amount (numeric)

version_number (int)
is_current (boolean)
valid_from (timestamp)
valid_to (timestamp)
```

---

#### C. employments

Stores employment details over time.

```
id (uuid, pk)
customer_id (uuid)
employer_name (text)
employment_type (text)

version_number (int)
is_current (boolean)
valid_from (timestamp)
valid_to (timestamp)
```

---

#### D. assets

Stores financial assets over time.

```
id (uuid, pk)
application_id (uuid)
asset_type (text)
asset_value (numeric)

version_number (int)
is_current (boolean)
valid_from (timestamp)
valid_to (timestamp)
```

---

#### E. liabilities

Stores liabilities over time.

```
id (uuid, pk)
application_id (uuid)
liability_type (text)
monthly_payment (numeric)

version_number (int)
is_current (boolean)
valid_from (timestamp)
valid_to (timestamp)
```

---

### Global Constraints

* No hard deletes
* No overwriting historical rows
* Exactly ONE row per logical entity may have `is_current = true`

---

## 6️⃣ Phase 2 — Versioning & Ingestion Logic

### Definition of “Update” (Critical)

An update **never modifies business columns**.

Instead:

1. Close the current version
2. Insert a new version

---

### Universal Update Algorithm

For a given logical entity:

#### Step 1 — Find current version

```
WHERE <logical identity> AND is_current = true
```

#### Step 2 — Close current version

```
is_current = false
valid_to = now()
```

#### Step 3 — Insert new version

```
version_number = previous + 1
is_current = true
valid_from = now()
valid_to = null
```

---

### Logical Identity Rules

Used to group versions of the same entity:

* income → `(customer_id, income_type)`
* employment → `(customer_id, employer_name)`
* asset → `(application_id, asset_type)`
* liability → `(application_id, liability_type)`

---

## 7️⃣ Phase 3 — Simple Web UI (Required for Testing)

Create a **minimal web interface** to interact with the system.

### Purpose of the UI

The UI is **not a product UI**.
It is a **testing and validation interface**.

---

### UI Requirements

* Single-page application
* Large text area to paste canonical JSON
* Submit / Update button
* Displays:

  * Success / error message
  * Version number created

---

### UI Flow

1. User pastes canonical JSON (e.g. new income data)
2. JSON is sent to backend API
3. Backend:

   * Determines target table
   * Applies versioning logic
   * Inserts data into Supabase
4. UI shows confirmation

---

### UI Must NOT

* Perform validation logic
* Modify canonical JSON
* Infer schema
* Contain database logic

---

## Code Structure (Strict Requirement)

Code must be **clean, modular, and extensible**.

### Suggested Structure

```
/db
  ├─ schema.sql
  ├─ supabase_client.py

/services
  ├─ versioning_service.py
  ├─ income_service.py
  ├─ employment_service.py
  ├─ asset_service.py

/api
  ├─ routes.py
  ├─ handlers.py

/ui
  ├─ index.html
  ├─ app.js

main.py
```

---

### Responsibility Separation

* `versioning_service`
  → shared logic for closing & creating versions

* Table-specific services
  → business-table logic only

* API layer
  → routing + orchestration

* UI
  → JSON input + feedback only

---

## 7️⃣ What You Must NOT Do

* ❌ No schema inference
* ❌ No JSON blob storage instead of tables
* ❌ No destructive updates
* ❌ No business logic inside UI
* ❌ No skipping version columns

---

## 8️⃣ Expected Final Behavior

After implementation:

* A user can submit:

  * Income version 1 (2020)
  * Income version 2 (2023)
* Both records exist simultaneously
* Latest data is easy to query
* Historical data is preserved
* The schema can later expand to full production scale

---

## Mental Model to Keep

> “Each table represents a **timeline of facts**, not a mutable object.”

Every insert is a **new point in time**.

---

### This is what i will provide in .env file
    
* Supabase credentials like:  
    * SUPABASE_URL=<supabase_project_url>
    * SUPABASE_SERVICE_ROLE_KEY=<service_role_key>
    * SUPABASE_ANON_KEY=<anon_key_if_needed>

``` 