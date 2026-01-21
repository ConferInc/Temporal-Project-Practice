import os
import shutil
import uuid
import traceback
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session
from pydantic import BaseModel

# Import Temporal client
from temporalio.client import Client

# Import App Modules
from app.workflows import LoanProcessWorkflow
from app.database import init_db, get_session
from app.models import User, Application
from app.auth import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from datetime import timedelta

app = FastAPI(title="Moxi Mortgage API", version="1.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*", 
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Setup Uploads Directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_ROOT = os.path.join(BASE_DIR, "..", "uploads")
os.makedirs(UPLOAD_ROOT, exist_ok=True)

# 2. Mount Static Files
app.mount("/static", StaticFiles(directory=UPLOAD_ROOT), name="static")

# === Startup Event ===
@app.on_event("startup")
def on_startup():
    init_db()
    # Admin Seeding
    try:
        session = next(get_session())
        admin_email = "admin@gmail.com"
        existing_admin = session.query(User).filter(User.email == admin_email).first()
        if not existing_admin:
            print(f"Seeding Admin User: {admin_email}")
            admin_user = User(
                email=admin_email,
                password_hash=get_password_hash("admin1234"),
                role="manager"
            )
            session.add(admin_user)
            session.commit()
    except Exception as e:
        print(f"Admin seeding failed: {e}")

# === Helper Classes ===
class ApprovalRequest(BaseModel):
    workflow_id: str
    approved: bool

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    email: str
    password: str

async def get_client():
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    return await Client.connect(temporal_host)

# === Auth Routes ===

@app.post("/auth/register", response_model=Token)
def register(user: UserCreate, session: Session = Depends(get_session)):
    # Check if user exists
    existing_user = session.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email, 
        password_hash=hashed_password,
        role="applicant" # Default role
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    # Generate Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email, "role": db_user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# === Application Routes ===

@app.post("/apply")
async def apply_for_loan(
    name: str = Form(...),
    email: str = Form(...),
    ssn: str = Form(...),
    income: str = Form(...),
    id_document: UploadFile = File(...),
    tax_document: UploadFile = File(...),
    pay_stub: UploadFile = File(...),
    credit_document: UploadFile = File(...),
    current_user: User = Depends(get_current_user), # Protected Route
    session: Session = Depends(get_session)
):
    try:
        # 1. Create a Unique Application ID
        app_id = f"loan-{uuid.uuid4()}"
        
        # 2. Create directory
        app_dir = os.path.join(UPLOAD_ROOT, app_id)
        os.makedirs(app_dir, exist_ok=True)
        
        # 3. Save Files Helper
        def save_file(uf: UploadFile, label: str):
            ext = os.path.splitext(uf.filename)[1]
            safe_name = f"{label}{ext}"
            path = os.path.join(app_dir, safe_name)
            with open(path, "wb") as buffer:
                shutil.copyfileobj(uf.file, buffer)
            return path, f"/static/{app_id}/{safe_name}"

        # Save all 4 files
        path_id, url_id = save_file(id_document, "ID_Document")
        path_tax, url_tax = save_file(tax_document, "Tax_Return")
        path_pay, url_pay = save_file(pay_stub, "Pay_Stub")
        path_credit, url_credit = save_file(credit_document, "Credit_Report")
        
        # 4. Prepare Workflow Data
        workflow_input = {
            "applicant_info": {
                "name": name,
                "email": email,
                "ssn": ssn,
                "stated_income": income
            },
            "file_paths": {
                "id_document": path_id,
                "tax_document": path_tax,
                "pay_stub": path_pay,
                "credit_document": path_credit
            },
            "public_urls": {
                "id_document": url_id,
                "tax_document": url_tax,
                "pay_stub": url_pay,
                "credit_document": url_credit
            }
        }

        # 5. Persist to Database (Hybrid Schema)
        new_app = Application(
            user_id=current_user.id,
            workflow_id=app_id,
            status="Submitted",
            loan_amount=0.0, # Placeholder, maybe extract from form later
            loan_metadata=workflow_input # Store the whole blob for flexibility
        )
        session.add(new_app)
        session.commit()
        
        # 6. Start Workflow
        client = await get_client()
        try:
            await client.start_workflow(
                LoanProcessWorkflow.run,
                workflow_input,
                id=app_id,
                task_queue="loan-application-queue",
            )
        except Exception as wf_error:
            # Rollback DB if workflow fails to start?
            # Ideally we mark it as failed in DB
            new_app.status = "Failed to Start"
            session.add(new_app)
            session.commit()
            raise wf_error
        
        return {
            "status": "submitted", 
            "workflow_id": app_id, 
            "message": "Application received and processing started."
        }

    except Exception as e:
        print(f"Upload Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/applications")
async def list_applications(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        if current_user.role == "manager":
            # Manager sees ALL applications
            apps = session.query(Application).order_by(Application.created_at.desc()).all()
        else:
            # Applicants see ONLY their own
            apps = session.query(Application).filter(Application.user_id == current_user.id).order_by(Application.created_at.desc()).all()
            
        return apps
    except Exception as e:
        print(f"Error listing applications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{workflow_id}")
async def get_status(workflow_id: str):
    client = await get_client()
    try:
        handle = client.get_workflow_handle(workflow_id)
        
        status = await handle.query(LoanProcessWorkflow.get_status)
        data = await handle.query(LoanProcessWorkflow.get_loan_data)
        
        return {
            "workflow_id": workflow_id,
            "status": status,
            "data": data,
        }
    except Exception as e:
        return {"status": "Unknown", "error": str(e)}

@app.get("/applications/{workflow_id}/structure")
async def get_application_structure(
    workflow_id: str,
    current_user: User = Depends(get_current_user)
):
    # Only allow access if manager or owner (skipping owner check strictly for now, favoring manager access)
    app_dir = os.path.join(UPLOAD_ROOT, workflow_id)
    if not os.path.exists(app_dir):
        # Retrieve from DB to check if it exists but no files?
        # For now, just 404
        raise HTTPException(status_code=404, detail="Application files not found")
    
    structure = []
    # Flat structure for this app
    for f in os.listdir(app_dir):
        if os.path.isfile(os.path.join(app_dir, f)):
            structure.append({
                "name": f,
                "type": "file",
                "url": f"/static/{workflow_id}/{f}"
            })
    return structure

@app.get("/applications/{workflow_id}/history")
async def get_application_history(workflow_id: str):
    client = await get_client()
    try:
        handle = client.get_workflow_handle(workflow_id)
        events = []
        async for event in handle.fetch_history_events():
             # Basic event info
             events.append({
                 "id": event.event_id,
                 "type": event.event_type.name if hasattr(event.event_type, "name") else str(event.event_type),
                 "timestamp": str(event.event_time) if hasattr(event, "event_time") else ""
             })
        return events
    except Exception as e:
        print(f"History error: {e}")
        return []

@app.post("/review")
async def review_application(
    request: ApprovalRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "manager":
         raise HTTPException(status_code=403, detail="Only managers can review")

    # Update Database
    db_app = session.query(Application).filter(Application.workflow_id == request.workflow_id).first()
    if db_app:
        db_app.status = "Approved" if request.approved else "Rejected"
        session.add(db_app)
        session.commit()

    # Signal Workflow
    clients = await get_client()
    try:
        handle = clients.get_workflow_handle(request.workflow_id)
        await handle.signal(LoanProcessWorkflow.human_approval_signal, request.approved)
        return {"status": "signal_sent", "approved": request.approved}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/application/{workflow_id}")
async def delete_application(workflow_id: str):
    client = await get_client()
    try:
        handle = client.get_workflow_handle(workflow_id)
        
        try:
            await handle.terminate("User requested deletion")
        except:
            pass

        app_dir = os.path.join(UPLOAD_ROOT, workflow_id)
        if os.path.exists(app_dir) and os.path.isdir(app_dir):
            shutil.rmtree(app_dir)
            
        return {"status": "deleted", "workflow_id": workflow_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
