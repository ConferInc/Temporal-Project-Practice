# MISMO XML Structural Validator - Comprehensive Walkthrough

This document explains the architecture, file responsibilities, and the internal validation logic of the mortgage processing pipeline.

---

## 🏗️ System Architecture: The 3-Layer Gate

The system acts as a high-security gate for mortgage data. It ensures that only perfect, MISMO-compliant data reaches the downstream banking systems.

1.  **Layer 1: Logical Validation (`validator.py`)**: Checks if the data makes sense (e.g., does the name on the paystub match the borrower name?).
2.  **Layer 2: Structural & Path Validation (`verify_failures.py`)**: Checks if the XML structure is correct and data is in the right place (e.g., exactly one `DEAL` exists).
3.  **Layer 3: Schema Validation (`main.py` using XSD)**: Final check for technical compliance with the official MISMO v3.6 schema.

---

## 📂 File-by-File Walkthrough

| File Name                | Role                  | Responsibility                                                                                                                                                 |
| :----------------------- | :-------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`main.py`**            | **Orchestrator**      | It is the "brain" that runs the whole process. It loads JSON data, calls the validator, generates the XML, and then runs the final XSD check.                  |
| **`validator.py`**       | **Business Rules**    | Validates the "meaning" of data. It ensures identity verification, US mortgage compliance, and geographic consistency (USD currency, etc.).                    |
| **`generator.py`**       | **XML Architect**     | Translates the JSON data into a complex MISMO XML string. It handles Namespaces and ensures data follows the basic hierarchy.                                  |
| **`prompts.py`**         | **The Rule Book**     | Stores the `MISMO_VALIDATOR_SYSTEM_PROMPT`. This file serves as the master specification for what defines "Correct MISMO."                                     |
| **`verify_failures.py`** | **Compliance Engine** | **(Critical)** This is where the Python-based structural validation lives. It "stress-tests" the XML against intentional errors and enforces path-level rules. |

---

## 🧪 How Validation Works (The "Fail Loudly" Principle)

The logic in `verify_failures.py` uses **ElementTree** (a Python XML parser) to inspect the XML. Here is why specific cases pass or fail:

### 1. DEAL Integrity (Structural)

- **The Logic**: It scans the XML for `<mismo:DEAL>` tags.
- **PASS**: If count == 1.
- **FAIL**: If count > 1. This prevents data corruption where multiple loans might get mixed into a single file.

### 2. Path Awareness (Placement)

- **The Logic**: It specifically checks the "Immediate Children" of `DEAL`.
- **FAIL Case**: If it finds a `<NAME>` tag directly under `<DEAL>`, it fails. MISMO rules mandate that a name must be deeper inside `PARTIES/PARTY/INDIVIDUAL/NAME`.

### 3. Referential Integrity (XLink)

- **The Logic**: In MISMO, Roles and Parties are linked via IDs (links).
- **FAIL Case**: If a `ROLE` points to an ID like `Party_999` but no `PARTY` with that ID exists, the system flags an "Orphaned Role" error.

### 4. XSD Compliance (Ordering)

- **The Logic**: The official schema requires strict ordering.
- **FAIL Case**: If `StateCode` appears before `PostalCode`, the XSD validator rejects it even if the data itself is correct.

---

## 🚀 How to Run and Verify

1.  **Main Pipeline**: Run `python src/main.py`. This generates `final_output.json` with the full XML.
2.  **Compliance Proof**: Run `python src/verify_failures.py`. This will run the 5 categorization tests (Valid, Structural, Path, XSD) and show you a table of results.

---

**One-Line Principle:**  
_"Correct XML should pass easily; incorrect XML should fail loudly and precisely."_
