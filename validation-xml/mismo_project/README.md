# 🏦 Mortgage Document Validator & MISMO Generator

> **Production-ready engine to Validate, Standardize, and Verify Mortgage Data using strict MISMO v3.x rules.**

---

## 🚀 Quick Start

### 1. Install Dependencies

You only need Python 3.8+ and `lxml`:

```bash
pip install lxml
```

### 2. Run the Main Pipeline

Process valid data and generate compliant XML:

```bash
cd src
python main.py
```

_Outputs `final_output.json` with generated MISMO XML._

### 3. Run Structural Compliance Tests

Verify that structural/path violations are correctly detected:

```bash
cd src
python verify_failures.py
```

_Demonstrates the "Fail Loudly" principle for Multiple DEALs, Orphaned Roles, and Path Violations._

---

## 📖 System Architecture: The 3-Layer Gate

This project implements a multi-stage validation pipeline to ensure absolute data integrity.

### Layer 1: Logical Validation (`validator.py`)

Checks if the **content** makes sense.

- Identity match (Borrower vs Document Issuer).
- Jurisdiction checks (US only).
- Currency verification (USD).

### Layer 2: Structural & Path Validation (`verify_failures.py`)

Enforces **MISMO Structural Rules**.

- **DEAL Integrity**: Exactly one DEAL per loan.
- **Path Ownership**: Ensures data like `Borrower Name` lives only in authorized paths (`/PARTIES/PARTY/INDIVIDUAL/NAME`).
- **Referential Integrity**: Every ROLE must point to a valid PARTY.

### Layer 3: Technical Compliance (`main.py` + XSD)

Final check against the official **MISMO v3.6.1 Schema**.

- Enforces correct element ordering (e.g., `PostalCode` before `StateCode`).
- Validates against official XSD enums and nesting rules.

---

## 📂 Project Structure

| File/Folder                  | Description                                                       |
| :--------------------------- | :---------------------------------------------------------------- |
| **`data/`**                  | Input JSON samples (Canonical & Document Context).                |
| **`schemas/`**               | Official MISMO XSD files for schema validation.                   |
| **`src/main.py`**            | Pipeline orchestrator and XSD runner.                             |
| **`src/generator.py`**       | Logic to map JSON data into MISMO XML structure.                  |
| **`src/prompts.py`**         | Master specification/system prompt for MISMO rules.               |
| **`src/verify_failures.py`** | Dynamic structural validator and failure simulation suite.        |
| **`System_Walkthrough.md`**  | **(Deep Dive)** Detailed breakdown of every logic point and rule. |

---

## 🧪 Verification Proof

The system is designed to **fail loudly**. By running `verify_failures.py`, you can prove that:

1.  **Valid XML** passes cleanly.
2.  **Structural Violations** (like Multiple DEAL nodes) are rejected.
3.  **Path Violations** (misplaced data) are caught.
4.  **Schema Errors** (XSD sequence failures) are detected independently.

---

_Built for strict data integrity and industrial-grade mortgage compliance._
