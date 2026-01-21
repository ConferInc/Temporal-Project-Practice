# 🏦 Moxi Mortgage Auto-Underwriter

A production-ready **Loan Origination System** built with **FastAPI**, **Temporal**, and **React**.
This application automates the loan underwriting process using AI (OpenAI) to analyze applicant documents, perform cross-verification (e.g., Stated vs. Tax Income), and provide a premium "Manager Dashboard" for human-in-the-loop decision making.

## 🚀 Key Features

### 🌟 For Applicants
- **Secure Authentication**: Register and login to start applications (OAuth2/JWT).
- **Multi-Document Portal**: Securely upload ID, Tax Returns, and Pay Stubs in a streamlined multi-step wizard.
- **Instant Processing**: Receive immediate confirmation and tracking ID.

### 🧠 Intelligent Backend
- **Hybrid Persistence**:
    - **Structured Data**: Users and Application records stored in **PostgreSQL**.
    - **Workflow Logic**: Business process state managed by **Temporal**.
- **AI Analysis**: Uses GPT-4o to extract structured data (Income, Name, Credit Score) from PDFs.
- **Cross-Verification**: Automatically flags discrepancies between *Stated Income* (form) and *Verified Income* (Tax Return).
- **Logic Gates**:
    - **Auto-Reject**: Credit Score < 620.
    - **Auto-Approve**: Score > 720 & Income > $60k & No Mismatches.
    - **Manual Review**: All other cases sent to Underwriter.

### 👨‍💼 Manager Dashboard
- **Application Overview**: Monitor incoming applications in real-time.
- **Deep Dive View**:
    - **Verification Table**: See "Stated" vs "Verified" data side-by-side with automatic match/mismatch indicators.
    - **Document Viewer**: Toggle between Applicant's Tax Return, ID, and Pay Stubs instantly without downloading.
- **One-Click Decisioning**: Approve or Reject applications, triggering email notifications.

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI, Temporal.io SDK, SQLModel (ORM), PyPDF, OpenAI
- **Frontend**: React, Tailwind CSS, Lucide Icons, Framer Motion
- **Infrastructure**: Docker Compose, PostgreSQL (DB & Temporal Store), Elasticsearch (Visibility)

## 🏃‍♂️ How to Run

### 1. Prerequisites
- Docker & Docker Compose installed.
- OpenAI API Key.

### 2. Setup
Clone the repo and create your environment file:
```bash
git clone <repo-url>
cd temporal-loan-python
# Create .env file with:
# OPENAI_API_KEY=sk-proj-....
# DATABASE_URL=postgresql://postgres:temporal@postgres:5432/temporal (Optional overrides)
```

### 3. Start the System
```bash
docker-compose up -d --build
```
*Note: We map Temporal to port `9233` (host) -> `7233` (container) to avoid conflicts on Windows. Docker containers talk internally on `7233`.*

### 4. Running Scripts Locally (Optional)
If you want to run `worker.py` or scripts from your host machine (outside Docker), set the env var:
```bash
# Powershell
$env:TEMPORAL_HOST="localhost:9233"
python backend/app/worker.py
```

## 🧪 Testing with Generated Data

We include a script to generate realistic test/demo data for different scenarios.

1.  **Generate Data**:
    ```bash
    python generate_test_data.py
    ```
    This creates a `test_data/` folder with subfolders for each applicant.

2.  **Test Personas**:
    *   **Alice_Perfect** (Auto-Approve): High Income ($120k), High Credit (780), consistent data.
    *   **Bob_Liar** (Auto-Reject): Low Credit (550), Income Mismatch.
    *   **Charlie_Manual** (Manual Review): Good Income ($70k), Moderate Credit (680). *Use this to test the Dashboard approval flow.*

3.  **Run the Flow**:
    *   Open User Portal (`http://localhost:3000`).
    *   **New**: Register for an account first!
    *   Fill in the form data.
    *   Upload the corresponding 4 PDFs from `test_data/[Name]/`.
    *   Submit and watch the status update!

### 5. Access the App
- **Applicant Dashboard**: [http://localhost:3000](http://localhost:3000)
    - *View and track your applications.*
- **Manager Dashboard**: [http://localhost:3000/manager](http://localhost:3000/manager)
    - *Review and approve loan requests.*
- **Apply for Loan**: [http://localhost:3000/apply](http://localhost:3000/apply)
- **Temporal UI**: [http://localhost:8080](http://localhost:8080) (Debug workflows)
- **API Docs**: [http://localhost:3001/docs](http://localhost:3001/docs)

## 📂 Project Structure

```
temporal-loan-python/
├── backend/
│   ├── app/
│   │   ├── main.py          # API & File Handling
│   │   ├── auth.py          # Authentication Logic (JWT, Hashing)
│   │   ├── models.py        # Database Models (User, Application)
│   │   ├── database.py      # Database Connection & Init
│   │   ├── worker.py        # Temporal Worker & Retry Logic
│   │   ├── workflows.py     # LoanProcessWorkflow (The Business Logic)
│   │   ├── activities.py    # AI Extraction Activities
│   └── uploads/             # (Ignored) Storage for uploaded PDFs
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── UserPortal.jsx       # Multi-step Application Wizard
│   │   │   ├── ManagerDashboard.jsx # Underwriter UI with Doc Viewer
├── generate_test_data.py    # Test Data Generator
├── docker-compose.yml       # Orchestration
└── .gitignore               # Build & Data Exclusions
```
