# 🏦 Moxi Mortgage Auto-Underwriter

A production-ready **Loan Origination System** built with **FastAPI**, **Temporal**, and **React**.
This application automates the loan underwriting process using AI (OpenAI) to analyze applicant documents, perform cross-verification (e.g., Stated vs. Tax Income), and provide a premium "Manager Dashboard" for human-in-the-loop decision making.

## 🚀 Key Features

### 🌟 For Applicants
- **Multi-Document Portal**: Securely upload ID, Tax Returns, and Pay Stubs in a streamlined multi-step wizard.
- **Instant Processing**: Receive immediate confirmation and tracking ID.

### 🧠 Intelligent Backend
- **AI Analysis**: uses GPT-4o to extract structured data (Income, Name, Credit Score) from PDFs.
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

- **Backend**: Python, FastAPI, Temporal.io SDK, PyPDF, OpenAI
- **Frontend**: React, Tailwind CSS, Lucide Icons, Framer Motion
- **Infrastructure**: Docker Compose, PostgreSQL (Temporal Store), Elasticsearch (Visibility)

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
```

### 3. Start the System
```bash
docker-compose up -d --build
```
*Note: The first build installs dependencies and may take a few minutes.*

### 4. Generate Test Data
We provide a script to generate realistic test "personas" (folders containing Tax Returns, IDs, etc.):

```bash
# Install fpdf locally if needed: pip install fpdf
python generate_test_data.py
```
This creates a `test_data/` folder with:
- `Alice_Perfect`: High income, perfect credit match.
- `Bob_Liar`: Stated Income $100k, but Tax Return shows $30k (Tests Fraud Detection).

### 5. Access the App
- **User Portal**: [http://localhost:3000](http://localhost:3000) (Apply here!)
- **Manager Dashboard**: [http://localhost:3000/manager](http://localhost:3000/manager) (Review here!)
- **Temporal UI**: [http://localhost:8080](http://localhost:8080) (Debug workflows)

## 📂 Project Structure

```
temporal-loan-python/
├── backend/
│   ├── app/
│   │   ├── main.py          # API & File Handling
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
