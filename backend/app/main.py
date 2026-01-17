import os
import shutil
import uuid
import traceback
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from temporalio.client import Client
from fastapi.middleware.cors import CORSMiddleware

# Import Workflow
from app.workflows import LoanProcessWorkflow

app = FastAPI(title="Moxi Mortgage API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

class ApprovalRequest(BaseModel):
    workflow_id: str
    approved: bool

async def get_client():
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    return await Client.connect(temporal_host)

@app.post("/apply")
async def apply_for_loan(
    name: str = Form(...),
    email: str = Form(...),
    ssn: str = Form(...),
    income: float = Form(...),
    id_document: UploadFile = File(...),
    tax_document: UploadFile = File(...),
    pay_stub: UploadFile = File(...)
):
    try:
        # 1. Create a Unique Application ID
        app_id = f"loan-{uuid.uuid4()}"
        
        # 2. Create a specific directory for this application
        # Structure: uploads/loan-1234/...
        app_dir = os.path.join(UPLOAD_ROOT, app_id)
        os.makedirs(app_dir, exist_ok=True)
        
        # 3. Helper to save file
        def save_file(uf: UploadFile, label: str):
            ext = os.path.splitext(uf.filename)[1]
            safe_name = f"{label}{ext}"
            path = os.path.join(app_dir, safe_name)
            with open(path, "wb") as buffer:
                shutil.copyfileobj(uf.file, buffer)
            return path, safe_name

        # Save all 3 files
        path_id, name_id = save_file(id_document, "ID_Document")
        path_tax, name_tax = save_file(tax_document, "Tax_Return")
        path_pay, name_pay = save_file(pay_stub, "Pay_Stub")
        
        # 4. Start Workflow
        client = await get_client()
        
        # We pass a Dict of data now, not just one path
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
                "pay_stub": path_pay
            },
            "public_urls": {
                "id_document": f"/static/{app_id}/{name_id}",
                "tax_document": f"/static/{app_id}/{name_tax}",
                "pay_stub": f"/static/{app_id}/{name_pay}"
            }
        }
        
        await client.start_workflow(
            LoanProcessWorkflow.run,
            workflow_input,
            id=app_id,
            task_queue="loan-application-queue",
        )
        
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
async def list_applications():
    client = await get_client()
    try:
        results = []
        async for workflow in client.list_workflows("WorkflowType='LoanProcessWorkflow'"):
            if workflow.status.name == "RUNNING" or workflow.status.name == "COMPLETED":
                results.append({
                    "workflow_id": workflow.id,
                    "run_id": workflow.run_id,
                    "status": workflow.status.name,
                    "start_time": workflow.start_time,
                })
        results.sort(key=lambda x: x["start_time"], reverse=True)
        return results
    except Exception as e:
        print(f"Error listing workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{workflow_id}")
async def get_status(workflow_id: str):
    client = await get_client()
    try:
        handle = client.get_workflow_handle(workflow_id)
        
        status = await handle.query(LoanProcessWorkflow.get_status)
        data = await handle.query(LoanProcessWorkflow.get_loan_data)
        
        # Return full data structure for new dashboard
        return {
            "workflow_id": workflow_id,
            "status": status,
            "data": data, # Will include the new structured data
        }
    except Exception as e:
        return {"status": "Unknown", "error": str(e)}

@app.post("/review")
async def review_application(request: ApprovalRequest):
    client = await get_client()
    try:
        handle = client.get_workflow_handle(request.workflow_id)
        await handle.signal(LoanProcessWorkflow.human_approval_signal, request.approved)
        return {"status": "signal_sent", "approved": request.approved}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/application/{workflow_id}")
async def delete_application(workflow_id: str):
    client = await get_client()
    try:
        handle = client.get_workflow_handle(workflow_id)
        
        # Terminate first
        try:
            await handle.terminate("User requested deletion")
        except:
            pass

        # Cleanup Disk (Delete the whole folder)
        # uploads/loan-1234
        app_dir = os.path.join(UPLOAD_ROOT, workflow_id)
        if os.path.exists(app_dir) and os.path.isdir(app_dir):
            shutil.rmtree(app_dir)
            
        return {"status": "deleted", "workflow_id": workflow_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))