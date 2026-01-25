# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Moxi Mortgage Auto-Underwriter - a loan origination system that automates underwriting using Temporal workflows and OpenAI for document analysis. The system uses a "Pyramid Architecture" with hierarchical workflows: CEO (parent) orchestrates Manager workflows (children), which execute MCP Activities (workers).

## Commands

### Run the Full Stack
```bash
docker-compose up -d --build
```

### Run Worker Locally (outside Docker)
```powershell
$env:TEMPORAL_HOST="localhost:9233"
python backend/app/temporal/worker.py
```

### Generate Test Data
```bash
python generate_test_data.py
```
Creates test personas in `test_data/`: Alice_Perfect (auto-approve), Bob_Liar (auto-reject), Charlie_Manual (manual review).

### Frontend Development
```bash
cd frontend
npm run dev      # Start dev server
npm run build    # Production build
npm run lint     # ESLint
```

### Access Points
- Frontend: http://localhost:3000
- API Docs: http://localhost:3001/docs
- Temporal UI: http://localhost:8088
- Admin login: admin@gmail.com / admin1234

## Architecture

```
Frontend (React:3000) → Backend (FastAPI:3001) → Temporal (7233)
                              ↓                        ↓
                         PostgreSQL              Elasticsearch
```

### Pyramid Architecture (Temporal Workflows)

The system uses a hierarchical "Pyramid" workflow structure:

```
Level 1: CEO (LoanLifecycleWorkflow)
    └── Orchestrates entire loan lifecycle
    └── Contains human approval gate
    └── Contains borrower signature gate

Level 2: Managers (Child Workflows)
    ├── LeadCaptureWorkflow - Creates loan file, sends welcome email, AI document analysis
    └── ProcessingWorkflow - Generates Initial Disclosures, verifies documents

Level 3: Workers (MCP Activities)
    ├── mcp_comms - send_email, send_sms
    ├── mcp_encompass - create_loan_file, push_field_update
    ├── mcp_docgen - generate_document
    └── legacy - analyze_document, read_pdf_content
```

### Loan Stage State Machine

```
LEAD_CAPTURE → (human approval) → PROCESSING → UNDERWRITING (signature wait) → CLOSING → ARCHIVED
                    ↓ (rejected)
                 ARCHIVED
```

Defined in `backend/app/models/sql.py` as `LoanStage` enum.

### Key Backend Files

- `temporal/workflows/ceo.py` - `LoanLifecycleWorkflow`: Parent workflow with signals (`human_approval`, `borrower_signature`, `update_field`) and queries
- `temporal/workflows/managers.py` - `LeadCaptureWorkflow`, `ProcessingWorkflow`: Child workflows
- `temporal/workflows/legacy.py` - `LoanProcessWorkflow`: Original flat workflow (backward compatible)
- `temporal/activities/` - MCP activities organized by domain (comms, encompass, docgen, legacy)
- `api/routes/applications.py` - REST endpoints including `/apply`, `/review`, `/sign`

### Workflow Signals

The CEO workflow accepts these signals:
- `human_approval(approved: bool)` - Manager approves/rejects application
- `borrower_signature(signed: bool)` - Borrower signs Initial Disclosures
- `update_field(field_name, value)` - Real-time field updates from manager dashboard

### File Handling

Uploads saved to `/backend/uploads/{workflow_id}/{label}.pdf`, served at `/static/{workflow_id}/`. Generated documents (Initial Disclosures) are saved to the same location.

## Environment Variables

- `OPENAI_API_KEY` or `LITELLM_API_KEY` - Required for AI document analysis
- `LITELLM_BASE_URL` - Optional LiteLLM proxy URL
- `TEMPORAL_HOST` - Temporal server address (default: `temporal:7233` in Docker, `localhost:9233` on host)
- `DATABASE_URL` - PostgreSQL connection (default configured in docker-compose)

## Port Mapping Note

Temporal uses port 9233 on host → 7233 in container to avoid Windows conflicts. Docker services communicate internally on 7233.

## Temporal Workflow Rules

When modifying workflows:
- Use `workflow.now()` instead of `datetime.utcnow()` for determinism
- Import non-workflow code inside `with workflow.unsafe.imports_passed_through():`
- Activities must be decorated with `@activity.defn` and called via `workflow.execute_activity()`
- Child workflows called via `workflow.execute_child_workflow()`
