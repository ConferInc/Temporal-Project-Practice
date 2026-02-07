# Phase 2: Supabase Memory Layer Integration

## Task Overview
Build a persistence layer using Supabase to store loan state across multiple document ingestions, enabling multi-document merging and audit trails.

## Context
Currently, the pipeline processes documents in isolation and outputs JSON/XML to disk. We need database persistence to:
1. Store loan state across multiple document ingestions
2. Enable "multi-document merging" (W-2 + URLA + Bank Statement → single loan)
3. Track audit trails (document history, timestamps)
4. Support concurrent processing (Temporal workflows)

## Database Schema

```sql
CREATE TABLE loans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    loan_number TEXT UNIQUE,
    borrower_ssn TEXT,  -- For identity resolution
    canonical_data JSONB NOT NULL,
    mismo_xml TEXT,
    document_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB  -- {documents: [{type, filename, processed_at}]}
);

CREATE INDEX idx_loans_ssn ON loans(borrower_ssn);
CREATE INDEX idx_loans_loan_number ON loans(loan_number);
```

## Implementation Tasks

### Task 1: Create Supabase Client Wrapper
**File**: `src/db/supabase_client.py`

```python
from typing import Optional, Dict, List
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

class SupabaseClient:
    """Singleton database client for loan persistence"""
    _instance: Optional['SupabaseClient'] = None
    _client: Optional[Client] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            if not url or not key:
                raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
            self._client = create_client(url, key)

    def get_loan_by_id(self, loan_id: str) -> Optional[Dict]:
        """Fetch loan by UUID"""
        response = self._client.table("loans").select("*").eq("id", loan_id).execute()
        return response.data[0] if response.data else None

    def get_loan_by_number(self, loan_number: str) -> Optional[Dict]:
        """Fetch loan by loan number"""
        response = self._client.table("loans").select("*").eq("loan_number", loan_number).execute()
        return response.data[0] if response.data else None

    def get_loan_by_ssn(self, ssn: str) -> Optional[Dict]:
        """Find loan by borrower SSN (for merging)"""
        response = self._client.table("loans").select("*").eq("borrower_ssn", ssn).execute()
        return response.data[0] if response.data else None

    def create_loan(self, canonical_data: Dict, mismo_xml: str, metadata: Dict) -> str:
        """Insert new loan, return UUID"""
        borrower_ssn = canonical_data.get('deal', {}).get('parties', [{}])[0].get('individual', {}).get('ssn')
        loan_number = canonical_data.get('deal', {}).get('identifiers', {}).get('loan_id')

        response = self._client.table("loans").insert({
            "loan_number": loan_number,
            "borrower_ssn": borrower_ssn,
            "canonical_data": canonical_data,
            "mismo_xml": mismo_xml,
            "document_count": 1,
            "metadata": metadata
        }).execute()

        return response.data[0]['id']

    def update_loan_state(self, loan_id: str, canonical_data: Dict, mismo_xml: str) -> None:
        """Update existing loan (merge logic)"""
        # Get current document count
        existing = self.get_loan_by_id(loan_id)
        if not existing:
            raise ValueError(f"Loan {loan_id} not found")

        new_count = existing['document_count'] + 1

        self._client.table("loans").update({
            "canonical_data": canonical_data,
            "mismo_xml": mismo_xml,
            "document_count": new_count,
            "updated_at": "NOW()"
        }).eq("id", loan_id).execute()

    def list_loans(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Paginated loan listing"""
        response = self._client.table("loans").select("*").order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        return response.data

    def health_check(self) -> bool:
        """Verify database connectivity"""
        try:
            self._client.table("loans").select("id").limit(1).execute()
            return True
        except Exception:
            return False
```

### Task 2: Update Pipeline Integration
**File**: `tools/unified_extraction.py`

Add the following logic after MISMO generation:

```python
from src.db.supabase_client import SupabaseClient
from datetime import datetime
import os

# ... existing code ...

def unified_extract(file_path: str, loan_id: Optional[str] = None):
    # ... existing processing (classification, extraction, MISMO generation) ...

    # NEW: Persist to database
    db = SupabaseClient()

    if loan_id:
        # Update existing loan
        existing = db.get_loan_by_id(loan_id)
        if not existing:
            raise ValueError(f"Loan {loan_id} not found")

        # Simple merge for Phase 2 (deep merge in Phase 3)
        merged_canonical = {**existing['canonical_data'], **canonical_data}
        db.update_loan_state(loan_id, merged_canonical, mismo_xml)

        return {
            **result,
            "loan_id": loan_id,
            "merge_status": "updated"
        }
    else:
        # Check if borrower exists (by SSN)
        borrower_ssn = canonical_data.get('deal', {}).get('parties', [{}])[0].get('individual', {}).get('ssn')

        if borrower_ssn:
            existing = db.get_loan_by_ssn(borrower_ssn)
            if existing:
                # Merge with existing loan
                loan_id = existing['id']
                merged_canonical = {**existing['canonical_data'], **canonical_data}
                db.update_loan_state(loan_id, merged_canonical, mismo_xml)

                return {
                    **result,
                    "loan_id": loan_id,
                    "merge_status": "merged_by_ssn"
                }

        # Create new loan
        metadata = {
            "documents": [{
                "type": document_type,
                "filename": os.path.basename(file_path),
                "processed_at": datetime.utcnow().isoformat()
            }]
        }
        loan_id = db.create_loan(canonical_data, mismo_xml, metadata)

        return {
            **result,
            "loan_id": loan_id,
            "merge_status": "created"
        }
```

### Task 3: Update FastMCP Server
**File**: `server.py`

Add new MCP tools:

```python
from src.db.supabase_client import SupabaseClient

@mcp.tool()
def list_loans(limit: int = 100) -> dict:
    """
    List all processed loans with pagination.

    Args:
        limit: Maximum number of loans to return (default 100)

    Returns:
        dict: {"loans": [...], "count": N}
    """
    db = SupabaseClient()
    loans = db.list_loans(limit=limit)

    # Strip canonical_data for list view (too large)
    loan_summaries = []
    for loan in loans:
        loan_summaries.append({
            "id": loan['id'],
            "loan_number": loan.get('loan_number'),
            "borrower_ssn": loan.get('borrower_ssn', 'N/A')[:7] + "**" if loan.get('borrower_ssn') else None,  # Masked
            "document_count": loan['document_count'],
            "created_at": loan['created_at'],
            "updated_at": loan['updated_at']
        })

    return {"loans": loan_summaries, "count": len(loan_summaries)}

@mcp.tool()
def get_loan_details(loan_id: str) -> dict:
    """
    Get full loan data by ID.

    Args:
        loan_id: UUID of the loan

    Returns:
        dict: Full loan object with canonical_data and mismo_xml
    """
    db = SupabaseClient()
    loan = db.get_loan_by_id(loan_id)

    if not loan:
        return {"error": "Loan not found", "loan_id": loan_id}

    return loan
```

### Task 4: Environment Configuration
**File**: `.env.template`

Create template for environment variables:

```
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here

# OpenAI API (for LLM extraction - Phase 1)
OPENAI_API_KEY=your-openai-key-here
```

## Acceptance Criteria

- [ ] Process URLA document → Creates new loan in Supabase with `loan_id`
- [ ] Process W-2 for same borrower (SSN match) → Updates existing loan (document_count increments)
- [ ] `list_loans()` returns paginated results with masked SSN
- [ ] `get_loan_details(id)` returns full canonical JSON + MISMO XML
- [ ] Connection errors return graceful error messages (not crashes)
- [ ] Environment variables loaded from `.env` file
- [ ] Health check passes before processing documents

## Dependencies

```bash
pip install supabase-py python-dotenv
```

## Testing Steps

1. **Setup Supabase**:
   - Create Supabase project (https://supabase.com)
   - Run schema migration (SQL above)
   - Copy URL and anon key to `.env`

2. **Test Create**:
   ```bash
   # Process URLA document
   python -c "from tools.unified_extraction import unified_extract; result = unified_extract('tests/data/urla_sample.pdf'); print(result['loan_id'])"
   ```
   - Verify row appears in Supabase dashboard
   - Check `document_count = 1`

3. **Test Update (SSN Match)**:
   ```bash
   # Process W-2 with matching SSN
   python -c "from tools.unified_extraction import unified_extract; result = unified_extract('tests/data/w2_sample.pdf'); print(result['merge_status'])"
   ```
   - Verify `merge_status = "merged_by_ssn"`
   - Check `document_count = 2`
   - Verify `metadata.documents` array has 2 entries

4. **Test MCP Tools**:
   ```bash
   # List loans
   from server import list_loans
   print(list_loans(limit=10))

   # Get loan details
   from server import get_loan_details
   print(get_loan_details("uuid-here"))
   ```

5. **Test Error Handling**:
   - Invalid Supabase credentials → Should raise `ValueError`
   - Network failure → Should log error and fail gracefully
   - Missing SSN in canonical data → Should still create loan (SSN optional)

## Success Metrics

- ✅ All acceptance criteria pass
- ✅ Zero crashes during database operations
- ✅ Loans persist across pipeline runs
- ✅ SSN-based merging works correctly
- ✅ FastMCP tools integrate with Supabase

## Next Steps (Phase 3)

After completion, update:
- `docs/TASK_LOG.md` → Mark Phase 2 as DONE
- `docs/ARCHITECTURE.md` → Add Supabase client to component list
- `CURRENT_TASK.md` → Update with Phase 3 tasks (Rule Engine)
