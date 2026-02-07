# Project Task Log

## Phase 1: The Laundry & Sorter
**Status:** ✅ COMPLETE
**Completed:** 2026-02-07
**Branch:** `feature/shrikanth`
**Commit:** `81bd654`

### Objectives
Build the pre-processing pipeline to standardize inputs and enable parallel processing.

### Deliverables
- ✅ **Image Converter** (`src/preprocessing/converter.py`)
  - Converts JPEG/PNG/TIFF → Searchable PDF
  - Uses RapidOCR for text layer extraction
  - Outputs to `temp/converted/`

- ✅ **PDF Splitter** (`src/preprocessing/splitter.py`)
  - Splits multi-page PDFs → Single-page chunks
  - Uses pypdf for page extraction
  - Outputs to `temp/chunks/`
  - Preserves page order

- ✅ **Mega-PDF Support** (`main.py`)
  - Entry point accepts multi-document PDFs
  - Routes to preprocessing pipeline
  - Handles temp directory management

- ✅ **Temporary File Structure**
  - `temp/converted/` - Image→PDF outputs
  - `temp/chunks/` - Split page outputs
  - Automatic cleanup on process start

### Testing
- ✅ Tested with 10-page Mega-PDF
- ✅ Tested with JPEG/PNG image inputs
- ✅ Verified page order preservation
- ✅ Confirmed text layer in converted PDFs

### Outcome
Pre-processing pipeline is **production-ready**. Files flow cleanly from `Ingest → Converter → Splitter → temp/chunks/`. Ready for Phase 2 (Stateful Processing).

---

## Phase 2: Stateful Processing with Supabase
**Status:** 🚧 IN PROGRESS
**Started:** 2026-02-07
**Target Completion:** 2026-02-14
**Branch:** `feature/shrikanth`
**Owner:** Autonomous Coding Agent

### Objectives
Enable **stateful loan processing** by persisting data to Supabase. Support multi-document merging (e.g., URLA + W-2 + Bank Statement → Single Loan).

### Dependencies
- `supabase-py` library
- Supabase project (cloud or self-hosted)
- Environment variables: `SUPABASE_URL`, `SUPABASE_KEY`

### Deliverables
- [ ] **Database Client** (`src/db/supabase_client.py`)
  - Class `SupabaseDB` (Singleton pattern)
  - Method `get_loan_state(loan_id: str) -> dict`
  - Method `update_loan_state(loan_id: str, canonical_data: dict)`
  - Method `create_loan(canonical_data: dict) -> str` (returns loan_id)
  - Connection health check

- [ ] **Processor Orchestrator** (`src/logic/processor.py`)
  - Replaces loop logic in `main.py`
  - Logic flow: `fetch_db → split → extract → merge → save_db`
  - Handles SSN-based identity resolution
  - Error handling for DB connection failures

- [ ] **Database Schema Migration**
  - Create `loans` table in Supabase
  - Indexes on `borrower_ssn`, `loan_number`
  - JSONB column for `canonical_data`

- [ ] **Environment Configuration**
  - `.env.template` with Supabase variables
  - Update `requirements.txt` with `supabase-py`, `python-dotenv`

- [ ] **Integration**
  - Update `main.py` to call `processor.py`
  - FastMCP tools: `list_loans()`, `get_loan_details(loan_id)`

### Acceptance Criteria
- [ ] Process URLA → Creates new loan in Supabase
- [ ] Process W-2 (same SSN) → Merges with existing loan
- [ ] `document_count` increments on each merge
- [ ] Connection errors return graceful failures
- [ ] All changes committed to `feature/shrikanth`
- [ ] Changes pushed to remote

### Git Protocol (STRICT)
```bash
# Before starting
git status                           # Verify on feature/shrikanth
git pull origin feature/shrikanth    # Sync with remote

# After implementation
git add .
git commit -m "feat(db): implement supabase client and stateful processor"
git push origin feature/shrikanth

# Optional: Create PR
gh pr create --title "Phase 2: Supabase Integration" --body "Implements stateful loan processing"
```

---

## Phase 3: Zero-LLM Rule Engine
**Status:** 📅 PLANNED
**Target Start:** 2026-02-15
**Target Completion:** 2026-02-22

### Objectives
Replace LLM-based extraction with deterministic YAML rule engine.

### Deliverables (Planned)
- [ ] YAML rule definitions for 14 document types
- [ ] Rule engine executor (`src/extraction/rule_engine.py`)
- [ ] Merger with priority logic (`src/logic/merger.py`)
- [ ] Canonical assembler (`src/assembler/canonical_assembler.py`)
- [ ] Remove OpenAI dependencies from `requirements.txt`

### Success Metrics
- Zero API calls to OpenAI
- Deterministic outputs (same input = same output)
- Performance: <5s per loan (full pipeline)
- Test coverage: >80%

---

## Phase 4: Production Ready
**Status:** 📅 PLANNED
**Target Start:** 2026-03-01
**Target Completion:** 2026-03-15

### Deliverables (Planned)
- [ ] Temporal workflow integration
- [ ] FastMCP server enhancements (auth, rate limiting)
- [ ] Web UI dashboard (loan list, document viewer)
- [ ] Performance benchmarks
- [ ] Compliance audit logs (SOC 2)

---

## Risk Log

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| Supabase performance (large JSONB) | Medium | Index optimization, pagination | Monitoring |
| YAML rules insufficient for complex forms | High | Hybrid approach (rules + LLM fallback) | Planned for Phase 3 |
| Document classification errors | High | Confidence thresholds, manual review queue | Active |
| Temp file cleanup failures | Low | Graceful error handling, background cleanup | Resolved |

---

## Commit History (Phase 1 & 2)

| Commit | Date | Phase | Description |
|--------|------|-------|-------------|
| `81bd654` | 2026-02-07 | 1 | docs: Add architecture documentation |
| `2a97b54` | 2026-02-07 | 1 | Phase 1 completion |
| `ccfa338` | 2026-01-XX | 0 | Added TestSprite to the Repo |
