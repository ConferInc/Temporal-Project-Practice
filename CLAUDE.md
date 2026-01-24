# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Moxi Mortgage Auto-Underwriter - a loan origination system that automates underwriting using Temporal workflows and OpenAI for document analysis. The system processes loan applications through AI-powered document extraction, automatic approval logic, and human-in-the-loop manager review.

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

### Key Components

**Backend (`backend/app/`)**
- `main.py` - FastAPI app, CORS, router registration
- `api/routes/auth.py` - JWT authentication (register/login)
- `api/routes/applications.py` - `/apply` endpoint, application management
- `temporal/workflows.py` - `LoanProcessWorkflow` orchestration
- `temporal/activities.py` - AI extraction (OCR, GPT analysis), file operations
- `temporal/worker.py` - Temporal worker entry point
- `core/security.py` - JWT creation, bcrypt password hashing
- `models/sql.py` - SQLModel tables (User, Application)

**Frontend (`frontend/src/`)**
- `pages/` - LoginPage, RegisterPage, ApplicantDashboard, ManagerDashboard, ApplicationDetail
- `components/UserPortal.jsx` - Multi-step loan application wizard
- `context/AuthContext.jsx` - JWT token management

### Workflow State Machine

`LoanProcessWorkflow` processes applications through:
1. File organization (File Clerk activity)
2. Parallel document analysis (OCR + GPT extraction)
3. Decision logic:
   - Credit < 620 → Auto-Reject
   - Credit > 740 & Income > $60k → Auto-Approve
   - Otherwise → Pending Manual Review (waits for `human_approval_signal`)

Manager approval sends a signal to resume the workflow.

### File Handling

Uploads saved to `/backend/uploads/{app_id}/{label}.pdf`, served at `/static/{app_id}/`. File paths stored in `Application.loan_metadata` JSON field.

## Environment Variables

- `OPENAI_API_KEY` - Required for AI document analysis
- `TEMPORAL_HOST` - Temporal server address (default: `temporal:7233` in Docker, `localhost:9233` on host)
- `DATABASE_URL` - PostgreSQL connection (default configured in docker-compose)

## Port Mapping Note

Temporal uses port 9233 on host → 7233 in container to avoid Windows conflicts. Docker services communicate internally on 7233.
