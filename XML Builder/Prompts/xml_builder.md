You are a senior mortgage platform engineer.

I need you to design and implement a PRODUCTION-READY, MODULAR, and OPTIMIZED Python pipeline that generates a MISMO XML file from an existing Supabase (PostgreSQL) Loan Origination System database.

Context:

- Loan data is already normalized and stored in Supabase
- Supabase is the system of record
- MISMO XML must be generated ONLY from database values
- The system must support multiple borrowers, incomes, employments, and liabilities
- Python is the only implementation language

Database tables involved (simplified):

- applications (loan-level data)
- users / customers (borrowers)
- employment
- incomes
- liabilities
- document_versions (for audit/version tracking)

Requirements:

1. The solution MUST be modular and production-ready
2. Do NOT generate XML directly from database rows
3. First aggregate all related tables into a single canonical `LoanSnapshot` object
4. Implement a clear mapping layer that converts database enums/values to MISMO-compliant values
5. Use `lxml` for XML generation
6. The XML builder must follow MISMO structural hierarchy (MESSAGE → DEAL_SETS → DEAL_SET → DEAL → LOAN)
7. Support repeatable nodes:
   - PARTY (multiple borrowers)
   - EMPLOYMENT
   - INCOME
   - LIABILITY
8. Include a validation layer to ensure required data exists before XML generation
9. Code must be readable, testable, and scalable
10. No hardcoded magic strings — centralize constants and mappings

Expected Output:

- A clean folder/module structure, for example:
  - db/
    - supabase_client.py
    - fetchers.py
  - domain/
    - loan_snapshot.py
  - mapping/
    - enums.py
    - mismo_mapper.py
  - xml/
    - xml_builder.py
  - validation/
    - loan_validator.py
  - main.py (orchestrates the full pipeline)

Implementation Expectations:

- Show how data is fetched from Supabase
- Show how LoanSnapshot is constructed
- Show how mapping functions work
- Show how MISMO XML is generated
- Show how the final XML file is written to disk
- Keep the code concise but production-grade
- Add comments explaining why decisions are made (not what Python syntax does)

Constraints:

- Do NOT include document parsing or OCR
- Do NOT store MISMO XML in the database
- Do NOT assume UI or frontend involvement
- Focus strictly on backend XML generation

Goal:
The final code should be suitable for:

- AUS submission
- Investor delivery
- Compliance exports

Respond with:

- Folder structure
- Python code for each module
- Brief explanations for each component
