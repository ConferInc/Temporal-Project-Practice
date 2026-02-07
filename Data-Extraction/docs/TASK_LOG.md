# Project Task Log

## Phase 1: Cleanup & Pre-processing
**Status:** ✅ DONE
**Completed:** 2026-02-07
**Commit:** `2a97b54`

### Deliverables
- ✅ Built document classifier (`tools/classifier.py`) - Supports 14 document types
- ✅ Integrated OCR extraction (`tools/doctr_tool.py`)
- ✅ Created MISMO mapper (`tools/mismo_mapper.py`) - 98 rule mappings
- ✅ Established canonical schema (`resources/canonical_schema/schema.json`) - 315 lines
- ✅ Built schema registry singleton (`schema_registry.py`)
- ✅ Built enum validator (`enum_validator.py`)
- ✅ Exposed FastMCP server (`server.py`) - 5 MCP tools

### Outcome
Foundation ready for Supabase integration (Phase 2) and rule engine development (Phase 3).

---

## Phase 2: Supabase Integration
**Status:** ⏳ IN PROGRESS
**Target:** 2026-02-14
**Owner:** Autonomous Coding Agent

### Objective
Build persistence layer for loan state management across multiple document ingestions.

### Dependencies
- `supabase-py` library
- Supabase project (cloud or self-hosted)

### Deliverables
- [ ] Database client wrapper (`src/db/supabase_client.py`)
- [ ] CRUD operations (get/update/create/list loans)
- [ ] Database schema migration (loans table with JSONB)
- [ ] Integration with `unified_extraction.py` (persistence after MISMO generation)
- [ ] Environment configuration (`.env` template)
- [ ] FastMCP tool additions (`list_loans`, `get_loan_details`)

### Acceptance Criteria
- Process URLA → Creates new loan in Supabase
- Process W-2 for same borrower (SSN match) → Updates existing loan (merge logic)
- `list_loans()` returns paginated results
- Connection errors return graceful failures

---

## Phase 3: Zero-LLM Rule Engine
**Status:** 📅 PLANNED
**Target:** 2026-02-21

### Objective
Replace LLM-based extraction with deterministic YAML rule engine.

### Deliverables
- [ ] Document splitter (`splitter/doc_splitter.py`) - Multi-page → Single-page PDFs
- [ ] Pre-processing laundry (`laundry/image_converter.py`) - Image → PDF conversion
- [ ] YAML rule definitions (14 document types in `resources/rules/`)
- [ ] Rule engine executor (`engine/rule_engine.py`) - Pattern matching & field extraction
- [ ] Merger with priority logic (`merger/canonical_merger.py`) - W-2 > URLA
- [ ] Canonical assembler (`assembler/canonical_assembler.py`) - Flat → Nested JSON
- [ ] Remove LLM dependencies (`structure_extractor.py`, OpenAI API calls)

### Success Metrics
- Zero API calls to OpenAI
- Deterministic outputs (same input = same output)
- Performance: <5s per loan (full pipeline)
- Test coverage: >80%

---

## Phase 4: MCP Server & UI
**Status:** 📅 PLANNED
**Target:** 2026-03-01

### Objective
Production-ready API and monitoring dashboard.

### Deliverables
- [ ] Enhanced FastMCP server (authentication, rate limiting)
- [ ] Web UI dashboard (loan list, document viewer, audit trail)
- [ ] Temporal workflow integration (retry logic, monitoring)
- [ ] Performance benchmarks (latency, throughput)
- [ ] Compliance audit logs (SOC 2 requirements)

---

## Commit History

| Commit | Date | Description |
|--------|------|-------------|
| `2a97b54` | 2026-02-07 | Phase 1 completion |
| `ccfa338` | 2026-01-XX | Added TestSprite to the Repo |
| `9d6c72e` | 2026-01-XX | UI changes and full schema workflow |
| `2cf1857` | 2026-01-XX | Added wait_conditions into temporal |

---

## Risk Log

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| YAML rules insufficient for complex forms | High | Hybrid approach (rules + LLM fallback) | Monitoring |
| Supabase performance (large JSONB) | Medium | Index optimization, pagination | TBD |
| Document type classification errors | High | Confidence thresholds, manual review queue | Active |
| MISMO mapping rule gaps | Medium | Incremental rule additions, user reporting | Active |
