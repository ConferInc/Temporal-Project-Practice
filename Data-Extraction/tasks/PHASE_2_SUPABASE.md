# PHASE 2: Supabase Integration - Work Order

**Task ID:** PHASE-2
**Assigned To:** Autonomous Coding Agent (Claude Terminal)
**Branch:** `feature/shrikanth`
**Priority:** HIGH
**Estimated Effort:** 4-6 hours

---

## Objective

Implement **stateful loan processing** by integrating Supabase as the persistence layer. Enable the pipeline to:
1. Store loan data across multiple document ingestions
2. Merge new documents with existing loan records (SSN-based identity resolution)
3. Track audit metadata (document count, timestamps, processing history)

---

## Context

**Current State (Post-Phase 1):**
- Files flow through: `main.py → converter.py → splitter.py → temp/chunks/`
- Each document is processed in isolation
- No persistence layer (data lost after processing)
- No multi-document merging capability

**Desired State (Post-Phase 2):**
- `main.py` orchestrates processing via `processor.py`
- `processor.py` fetches existing loan state from Supabase
- New document data merges with existing data (if SSN matches)
- Final state saves back to Supabase with updated `document_count`

---

## Technical Specifications

### Task 1: Add Dependencies

**File:** `requirements.txt`

**Action:** Add the following dependencies:
```
supabase-py==2.9.0
python-dotenv==1.0.0
```

**Verification:**
```bash
pip install -r requirements.txt
```

---

### Task 2: Create Supabase Client

**File:** `src/db/supabase_client.py`

**Requirements:**

1. **Class `SupabaseDB` (Singleton Pattern)**
   - Single instance shared across the application
   - Lazy initialization (connect only when first used)

2. **Connection Management**
   - Load `SUPABASE_URL` and `SUPABASE_KEY` from environment (`.env` file)
   - Raise `ValueError` if environment variables are missing
   - Use `supabase.create_client(url, key)` to initialize client

3. **Required Methods:**

```python
class SupabaseDB:
    """Singleton database client for loan persistence."""

    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            # Load environment variables
            # Initialize Supabase client
            pass

    def get_loan_state(self, loan_id: str) -> dict:
        """
        Fetch existing loan data by loan_id (UUID).

        Args:
            loan_id: UUID string

        Returns:
            dict: Loan record with canonical_data, mismo_xml, document_count

        Raises:
            ValueError: If loan_id not found
        """
        pass

    def get_loan_by_ssn(self, borrower_ssn: str) -> dict:
        """
        Find loan by borrower SSN (for identity resolution).

        Args:
            borrower_ssn: Social Security Number (format: "123-45-6789")

        Returns:
            dict: Loan record if found, None otherwise
        """
        pass

    def create_loan(self, canonical_data: dict, mismo_xml: str = None) -> str:
        """
        Create a new loan record.

        Args:
            canonical_data: Nested canonical JSON structure
            mismo_xml: Optional MISMO 3.4 XML string

        Returns:
            str: UUID of created loan

        Process:
            1. Extract borrower_ssn from canonical_data
            2. Generate UUID for loan_id
            3. Insert into loans table
            4. Return loan_id
        """
        pass

    def update_loan_state(self, loan_id: str, canonical_data: dict, mismo_xml: str = None):
        """
        Update existing loan with new data (merge operation).

        Args:
            loan_id: UUID of existing loan
            canonical_data: New canonical data to merge
            mismo_xml: Updated MISMO XML

        Process:
            1. Fetch existing canonical_data
            2. Merge new data (deep merge, prefer new values)
            3. Increment document_count
            4. Update updated_at timestamp
            5. Save to database
        """
        pass

    def list_loans(self, limit: int = 100, offset: int = 0) -> list:
        """
        List all loans (paginated).

        Args:
            limit: Maximum number of loans to return
            offset: Number of records to skip

        Returns:
            list: List of loan records (sorted by created_at desc)
        """
        pass

    def health_check(self) -> bool:
        """
        Verify database connectivity.

        Returns:
            bool: True if connection successful, False otherwise
        """
        pass
```

**Database Schema (for reference):**
```sql
CREATE TABLE loans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    loan_number TEXT UNIQUE,
    borrower_ssn TEXT,
    canonical_data JSONB NOT NULL,
    mismo_xml TEXT,
    document_count INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

CREATE INDEX idx_loans_ssn ON loans(borrower_ssn);
CREATE INDEX idx_loans_loan_number ON loans(loan_number);
```

**Implementation Notes:**
- Use `supabase.table("loans").select("*").eq("id", loan_id).execute()` for queries
- Use `supabase.table("loans").insert({...}).execute()` for inserts
- Use `supabase.table("loans").update({...}).eq("id", loan_id).execute()` for updates
- Handle `response.data` which is a list (empty if no results)
- Extract `borrower_ssn` via: `canonical_data.get('deal', {}).get('parties', [{}])[0].get('individual', {}).get('ssn')`

---

### Task 3: Create Processor Orchestrator

**File:** `src/logic/processor.py`

**Requirements:**

1. **Function `process_loan_package(file_path: str, loan_id: str = None) -> dict`**

**Logic Flow:**
```
1. Initialize SupabaseDB client
2. If loan_id provided:
     a. Fetch existing loan state via get_loan_state(loan_id)
   Else:
     a. Extract text from first page (quick scan for SSN)
     b. If SSN found, check if loan exists via get_loan_by_ssn(ssn)
     c. If exists, set loan_id to existing loan's id
3. Split PDF via splitter.py (if multi-page)
4. Extract data from each page (placeholder: return mock data for now)
5. Merge extracted data:
     a. If loan_id exists: Deep merge with existing canonical_data
     b. Else: Use extracted data as-is
6. Generate MISMO XML (placeholder: return empty string for now)
7. Save to database:
     a. If loan_id exists: update_loan_state(loan_id, merged_data, xml)
     b. Else: create_loan(merged_data, xml)
8. Return result dict
```

**Function Signature:**
```python
def process_loan_package(file_path: str, loan_id: str = None) -> dict:
    """
    Orchestrate loan processing with stateful persistence.

    Args:
        file_path: Path to PDF or image file
        loan_id: Optional UUID of existing loan (for explicit updates)

    Returns:
        dict: {
            "loan_id": str,
            "status": "created" | "updated",
            "document_count": int,
            "canonical_data": dict,
            "mismo_xml": str
        }

    Process:
        1. Check if loan exists (by loan_id or SSN)
        2. Split file (if PDF with multiple pages)
        3. Extract data (mock for Phase 2)
        4. Merge with existing data (if loan exists)
        5. Save to Supabase
        6. Return result
    """
    pass
```

**Implementation Notes:**
- Import: `from src.preprocessing.splitter import split_pdf`
- Import: `from src.db.supabase_client import SupabaseDB`
- For Phase 2, extraction can return mock data:
  ```python
  # Placeholder extraction
  extracted_data = {
      "deal": {
          "parties": [{
              "individual": {
                  "ssn": "123-45-6789",
                  "first_name": "John",
                  "last_name": "Doe"
              }
          }]
      }
  }
  ```
- Deep merge function (simple version for Phase 2):
  ```python
  def deep_merge(existing: dict, new: dict) -> dict:
      """Merge two dicts, preferring new values."""
      merged = existing.copy()
      for key, value in new.items():
          if isinstance(value, dict) and key in merged:
              merged[key] = deep_merge(merged[key], value)
          else:
              merged[key] = value
      return merged
  ```

---

### Task 4: Update Main Entry Point

**File:** `main.py`

**Action:** Replace the processing loop with a call to `processor.py`

**Current Code (to replace):**
```python
# Old approach
if file_path.endswith('.pdf'):
    pages = split_pdf(file_path)
    # Process pages...
```

**New Code:**
```python
from src.logic.processor import process_loan_package

def main():
    file_path = "path/to/loan_package.pdf"

    # Process with Supabase integration
    result = process_loan_package(file_path)

    print(f"Loan ID: {result['loan_id']}")
    print(f"Status: {result['status']}")
    print(f"Document Count: {result['document_count']}")
```

---

### Task 5: Environment Configuration

**File:** `.env.template`

**Action:** Create template for environment variables

**Content:**
```
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here

# Optional: OpenAI API (for Phase 1 LLM extraction)
OPENAI_API_KEY=your-openai-key-here
```

**File:** `.env` (create locally, do NOT commit)

**Action:** Copy `.env.template` to `.env` and fill in actual values

---

### Task 6: FastMCP Server Integration (Optional)

**File:** `server.py`

**Action:** Add new MCP tools for database access

**New Tools:**
```python
from src.db.supabase_client import SupabaseDB

@mcp.tool()
def list_loans(limit: int = 100) -> dict:
    """
    List all processed loans.

    Args:
        limit: Maximum number of loans to return

    Returns:
        dict: {"loans": [...], "count": int}
    """
    db = SupabaseDB()
    loans = db.list_loans(limit=limit)

    # Strip large fields for list view
    summaries = []
    for loan in loans:
        summaries.append({
            "id": loan['id'],
            "loan_number": loan.get('loan_number'),
            "borrower_ssn": loan.get('borrower_ssn', 'N/A')[:7] + "**",  # Masked
            "document_count": loan['document_count'],
            "created_at": loan['created_at']
        })

    return {"loans": summaries, "count": len(summaries)}

@mcp.tool()
def get_loan_details(loan_id: str) -> dict:
    """
    Get full loan data by ID.

    Args:
        loan_id: UUID of the loan

    Returns:
        dict: Full loan object with canonical_data and mismo_xml
    """
    db = SupabaseDB()
    try:
        loan = db.get_loan_state(loan_id)
        return loan
    except ValueError as e:
        return {"error": str(e), "loan_id": loan_id}
```

---

## Acceptance Criteria

Before marking this task as complete, verify:

- [ ] **Dependency Installation**
  - `supabase-py` and `python-dotenv` in `requirements.txt`
  - `pip install -r requirements.txt` succeeds

- [ ] **Supabase Client**
  - `src/db/supabase_client.py` exists
  - All 7 methods implemented (`get_loan_state`, `get_loan_by_ssn`, `create_loan`, `update_loan_state`, `list_loans`, `health_check`, `__init__`)
  - Singleton pattern works (same instance on multiple calls)

- [ ] **Processor Orchestrator**
  - `src/logic/processor.py` exists
  - `process_loan_package()` function implemented
  - Handles both new loans and updates (SSN matching)

- [ ] **Main Integration**
  - `main.py` calls `processor.process_loan_package()`
  - No direct database calls in `main.py`

- [ ] **Environment Configuration**
  - `.env.template` exists with Supabase variables
  - `.env` file created locally (NOT committed)

- [ ] **Testing (Manual)**
  - Process a URLA PDF → New loan created in Supabase
  - Process a W-2 PDF (same SSN) → Existing loan updated, `document_count = 2`
  - Call `list_loans()` → Returns loan list
  - Call `get_loan_details(loan_id)` → Returns full loan data

- [ ] **Error Handling**
  - Missing environment variables → Raises `ValueError` with clear message
  - Invalid `loan_id` → Returns error dict (not crash)
  - Supabase connection failure → Logs error and fails gracefully

---

## Git Protocol (STRICT - DO NOT DEVIATE)

### Pre-Implementation Checklist

```bash
# 1. Verify you are on the correct branch
git branch
# Expected output: * feature/shrikanth

# If not on feature/shrikanth:
git checkout feature/shrikanth

# 2. Sync with remote
git pull origin feature/shrikanth

# 3. Verify clean working directory
git status
# Expected: No uncommitted changes (or only expected changes)
```

### Post-Implementation Checklist

```bash
# 1. Stage all changes
git add .

# 2. Verify staged files
git status
# Expected files:
#   new file:   src/db/supabase_client.py
#   new file:   src/logic/processor.py
#   modified:   main.py
#   modified:   requirements.txt
#   new file:   .env.template

# 3. Commit with semantic message
git commit -m "feat(db): implement supabase client and stateful processor

- Add SupabaseDB singleton client with CRUD operations
- Create processor.py orchestrator for stateful loan processing
- Integrate SSN-based identity resolution
- Update main.py to use processor instead of direct splitting
- Add .env.template for Supabase configuration

Implements Phase 2: Stateful Processing
Closes PHASE-2"

# 4. Push to remote
git push origin feature/shrikanth

# 5. (Optional) Create Pull Request
# Only if gh CLI is available:
gh pr create --title "Phase 2: Supabase Integration" \
             --body "Implements stateful loan processing with Supabase persistence. Enables multi-document merging via SSN matching." \
             --base main \
             --head feature/shrikanth
```

### Commit Message Format

**Required Structure:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Example:**
```
feat(db): implement supabase client and stateful processor

- Add SupabaseDB singleton client with CRUD operations
- Create processor.py orchestrator for stateful loan processing
- Integrate SSN-based identity resolution
- Update main.py to use processor instead of direct splitting
- Add .env.template for Supabase configuration

Implements Phase 2: Stateful Processing
Closes PHASE-2
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Scopes:**
- `db`: Database-related changes
- `api`: API changes
- `preprocessing`: Pre-processing pipeline
- `extraction`: Data extraction logic

---

## Testing Instructions

### Setup Supabase (One-Time)

1. **Create Supabase Project**
   - Go to https://supabase.com
   - Create new project
   - Copy Project URL and Anon Key

2. **Run Schema Migration**
   - Navigate to SQL Editor in Supabase dashboard
   - Paste the database schema (see Task 2)
   - Execute

3. **Configure Environment**
   - Copy `.env.template` to `.env`
   - Fill in `SUPABASE_URL` and `SUPABASE_KEY`

### Manual Testing

```bash
# Test 1: Create New Loan
python main.py --file "tests/data/urla_sample.pdf"
# Expected: New loan created, loan_id printed

# Test 2: Update Existing Loan (SSN Match)
python main.py --file "tests/data/w2_sample.pdf"
# Expected: Existing loan updated (if SSN matches), document_count = 2

# Test 3: List Loans
python -c "from src.db.supabase_client import SupabaseDB; db = SupabaseDB(); print(db.list_loans(limit=5))"
# Expected: List of loans (max 5)

# Test 4: Get Loan Details
python -c "from src.db.supabase_client import SupabaseDB; db = SupabaseDB(); print(db.get_loan_state('LOAN-UUID-HERE'))"
# Expected: Full loan object
```

---

## Success Metrics

- ✅ Zero crashes during database operations
- ✅ SSN-based merging works (same borrower → same loan)
- ✅ `document_count` increments correctly
- ✅ All changes committed to `feature/shrikanth`
- ✅ Changes successfully pushed to remote
- ✅ Code follows existing patterns (type hints, docstrings, error handling)

---

## Notes for the Coding Agent

1. **Do NOT modify**:
   - `src/preprocessing/converter.py` (already complete)
   - `src/preprocessing/splitter.py` (already complete)
   - `resources/canonical_schema/schema.json` (schema definition)
   - `resources/mismo_mapping/map_mismo_3_6.json` (mapping rules)

2. **Use existing patterns**:
   - Look at `src/preprocessing/converter.py` for code style
   - Follow type hints (Python 3.11+)
   - Add docstrings to all functions
   - Use `utils.logging.logger` for logging (if available)

3. **Error handling**:
   - Always use try/except for database operations
   - Log errors before raising
   - Return error dicts instead of crashing (where appropriate)

4. **Testing**:
   - Test with actual Supabase instance (not mocks)
   - Verify SSN extraction works with real canonical data
   - Check `document_count` increments

5. **Git**:
   - **CRITICAL:** Verify you are on `feature/shrikanth` before committing
   - Use the exact commit message format specified above
   - Push to `origin feature/shrikanth` (not `main`)

---

## Questions/Blockers

If you encounter any of the following, STOP and ask the user:

1. **Supabase credentials not available**
   - Cannot test without `SUPABASE_URL` and `SUPABASE_KEY`

2. **Unclear merge strategy**
   - If multiple loans exist with same SSN, which one to use?

3. **Missing extraction logic**
   - Phase 2 uses mock data, but if real extraction is needed, clarify scope

4. **Git conflicts**
   - If `git push` fails due to conflicts, request guidance

---

## Completion Checklist

Mark this task complete when:

- [ ] All files created as specified
- [ ] All acceptance criteria met
- [ ] Manual tests pass
- [ ] Code committed to `feature/shrikanth`
- [ ] Code pushed to remote
- [ ] `docs/TASK_LOG.md` updated (mark Phase 2 as COMPLETE)

**Next Phase:** Phase 3 (Zero-LLM Rule Engine)
