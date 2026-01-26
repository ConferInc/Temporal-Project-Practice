import os
import uuid
import traceback
from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException
from sqlmodel import Session, select

from app.api import deps
from app.models.sql import User, Application, LoanStage
from app.models.schemas import ApprovalRequest
from app.services import files, temporal
from app.temporal.workflows import LoanProcessWorkflow

# Pyramid Architecture: CEO Workflow
from app.temporal.workflows.ceo import LoanLifecycleWorkflow

# Pyramid Architecture: Manager Workflows (for signals)
from app.temporal.workflows.managers import LeadCaptureWorkflow



router = APIRouter()

@router.post("/apply")
async def apply_for_loan(
    name: str = Form(...),
    email: str = Form(...),
    ssn: str = Form(...),
    income: str = Form(...),
    id_document: UploadFile = File(...),
    tax_document: UploadFile = File(...),
    pay_stub: UploadFile = File(...),
    credit_document: UploadFile = File(...),
    use_pyramid: bool = Form(default=True),
    current_user: User = Depends(deps.get_current_user),
    session: Session = Depends(deps.get_session)
):
    """
    Submit a loan application.

    Args:
        use_pyramid: If True, uses the Pyramid Architecture (LoanLifecycleWorkflow).
                     If False (default), uses the original LoanProcessWorkflow.
    """
    try:
        # 1. Create a Unique Application ID
        app_id = f"loan-{uuid.uuid4()}"

        # 2. Save all 4 files
        path_id, url_id = files.save_application_file(app_id, id_document, "ID_Document")
        path_tax, url_tax = files.save_application_file(app_id, tax_document, "Tax_Return")
        path_pay, url_pay = files.save_application_file(app_id, pay_stub, "Pay_Stub")
        path_credit, url_credit = files.save_application_file(app_id, credit_document, "Credit_Report")

        # 3. Get funnel data from user's initial_metadata
        funnel_data = current_user.initial_metadata or {}
        property_value = float(funnel_data.get("property_value", 0))
        down_payment = float(funnel_data.get("down_payment", 0))
        loan_amount = float(funnel_data.get("loan_amount", property_value - down_payment))
        citizenship = funnel_data.get("citizenship", None)

        # 4. Prepare Workflow Data (include funnel financial data)
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
            },
            # Funnel data for DocGen and Processing
            "property_value": property_value,
            "down_payment": down_payment,
            "loan_amount": loan_amount,
            "citizenship": citizenship,
        }

        # 5. Persist to Database
        new_app = Application(
            user_id=current_user.id,
            workflow_id=app_id,
            status="Submitted",
            loan_stage=LoanStage.LEAD_CAPTURE.value if use_pyramid else None,
            loan_amount=loan_amount,  # Store actual loan amount from funnel
            loan_metadata=workflow_input
        )
        session.add(new_app)
        session.commit()

        # 6. Start Workflow
        client = await temporal.get_client()
        try:
            if use_pyramid:
                # Pyramid Architecture: Start CEO Workflow
                await client.start_workflow(
                    LoanLifecycleWorkflow.run,
                    workflow_input,
                    id=app_id,
                    task_queue="loan-application-queue",
                )
                workflow_type = "LoanLifecycleWorkflow (Pyramid)"
            else:
                # Original workflow (backward compatible)
                await client.start_workflow(
                    LoanProcessWorkflow.run,
                    workflow_input,
                    id=app_id,
                    task_queue="loan-application-queue",
                )
                workflow_type = "LoanProcessWorkflow (Original)"
        except Exception as wf_error:
            new_app.status = "Failed to Start"
            session.add(new_app)
            session.commit()
            raise wf_error

        return {
            "status": "submitted",
            "workflow_id": app_id,
            "workflow_type": workflow_type,
            "message": "Application received and processing started."
        }

    except Exception as e:
        print(f"Upload Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/applications")
async def list_applications(
    session: Session = Depends(deps.get_session),
    current_user: User = Depends(deps.get_current_user)
):
    try:
        if current_user.role == "manager":
            apps = session.query(Application).order_by(Application.created_at.desc()).all()
        else:
            apps = session.query(Application).filter(Application.user_id == current_user.id).order_by(Application.created_at.desc()).all()      
        return apps
    except Exception as e:
        print(f"Error listing applications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{workflow_id}")
async def get_status(
    workflow_id: str,
    session: Session = Depends(deps.get_session)
):
    client = await temporal.get_client()

    # Fetch SQL record for loan_metadata
    app_record = session.exec(
        select(Application).where(Application.workflow_id == workflow_id)
    ).first()

    loan_metadata = app_record.loan_metadata if app_record else {}
    sql_status = app_record.status if app_record else "Unknown"

    try:
        handle = client.get_workflow_handle(workflow_id)

        # Try Pyramid workflow queries first
        try:
            stage = await handle.query(LoanLifecycleWorkflow.get_current_stage)
            logs = await handle.query(LoanLifecycleWorkflow.get_logs)
            return {
                "workflow_id": workflow_id,
                "workflow_type": "Pyramid",
                "loan_stage": stage,
                "logs": logs,
                "status": sql_status,
                "data": loan_metadata,  # Include loan_metadata as 'data' for frontend compatibility
                "loan_metadata": loan_metadata,
            }
        except Exception:
            pass

        # Fallback to original workflow
        status = await handle.query(LoanProcessWorkflow.get_status)
        data = await handle.query(LoanProcessWorkflow.get_loan_data)

        return {
            "workflow_id": workflow_id,
            "workflow_type": "Original",
            "status": status,
            "data": data,
        }
    except Exception as e:
        # Even if Temporal fails, return SQL data if available
        if app_record:
            return {
                "workflow_id": workflow_id,
                "workflow_type": "Unknown",
                "status": sql_status,
                "data": loan_metadata,
                "loan_metadata": loan_metadata,
                "error": str(e)
            }
        return {"status": "Unknown", "error": str(e)}

@router.get("/applications/{workflow_id}/structure")
async def get_application_structure(
    workflow_id: str,
    current_user: User = Depends(deps.get_current_user)
):
    app_dir = os.path.join(files.get_upload_root(), workflow_id)
    if not os.path.exists(app_dir):
        raise HTTPException(status_code=404, detail="Application files not found")
    
    structure = []
    for f in os.listdir(app_dir):
        if os.path.isfile(os.path.join(app_dir, f)):
            structure.append({
                "name": f,
                "type": "file",
                "url": f"/static/{workflow_id}/{f}"
            })
    return structure


@router.patch("/applications/{workflow_id}/fields")
async def update_application_field(
    workflow_id: str,
    field_update: dict,
    session: Session = Depends(deps.get_session),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Update a field in a running loan application.
    Sends signal to Temporal workflow and updates SQL database.

    Accepts: {"field": str, "value": any}
    """
    if current_user.role != "manager":
        raise HTTPException(status_code=403, detail="Only managers can update fields")

    field_name = field_update.get("field")
    field_value = field_update.get("value")

    if not field_name:
        raise HTTPException(status_code=400, detail="Field name is required")

    # 1. Update SQL Database
    app_record = session.exec(
        select(Application).where(Application.workflow_id == workflow_id)
    ).first()

    if not app_record:
        raise HTTPException(status_code=404, detail="Application not found")

    # Update loan_metadata JSON field
    metadata = app_record.loan_metadata or {}

    # Handle nested applicant_info fields
    if field_name in ["name", "email", "ssn", "stated_income"]:
        if "applicant_info" not in metadata:
            metadata["applicant_info"] = {}
        metadata["applicant_info"][field_name] = field_value
    else:
        metadata[field_name] = field_value

    app_record.loan_metadata = metadata
    session.add(app_record)
    session.commit()

    # 2. Signal Temporal Workflow (Pyramid architecture)
    try:
        client = await temporal.get_client()

        # Signal the CEO workflow directly (gate is at CEO level)
        if app_record.loan_stage:
            handle = client.get_workflow_handle(workflow_id)
            await handle.signal("update_field", field_name, field_value)
    except Exception as e:
        print(f"Warning: Failed to signal workflow {workflow_id}: {e}")
        # DB update succeeded, workflow signal is best-effort

    return {
        "message": f"Field '{field_name}' updated successfully",
        "workflow_id": workflow_id,
        "field": field_name,
        "value": field_value
    }


@router.post("/review")
async def review_application(
    request: ApprovalRequest,
    session: Session = Depends(deps.get_session),
    current_user: User = Depends(deps.get_current_user)
):
    if current_user.role != "manager":
        raise HTTPException(status_code=403, detail="Only managers can review applications")

    # 1. Update DB Status immediately
    app_record = session.exec(select(Application).where(Application.workflow_id == request.workflow_id)).first()
    if not app_record:
        raise HTTPException(status_code=404, detail="Application not found")

    # Set specific status based on decision (Golden Path alignment)
    if request.approved:
        app_record.status = "Processing"  # More specific than "Approved by Manager"
    else:
        app_record.status = "Rejected by Manager"
    app_record.decision_reason = request.reason

    # Update loan_stage for Pyramid workflows
    if app_record.loan_stage:
        if request.approved:
            app_record.loan_stage = LoanStage.PROCESSING.value
        else:
            app_record.loan_stage = LoanStage.ARCHIVED.value

    session.add(app_record)
    session.commit()

    status_msg = "Approved" if request.approved else "Rejected"

    # 2. Signal Temporal Workflow
    try:
        client = await temporal.get_client()
        handle = client.get_workflow_handle(request.workflow_id)

        # Try Pyramid workflow signal first (signal the PARENT CEO workflow)
        is_pyramid = app_record.loan_stage is not None
        if is_pyramid:
            # Signal the CEO workflow directly (not the child)
            # The gate is now at the CEO level
            await handle.signal("human_approval", request.approved)
        else:
            # Original workflow signal
            await handle.signal("approve_signal", request.approved)

    except Exception as e:
        print(f"Warning: Failed to signal workflow {request.workflow_id}: {e}")
        # We generally don't want to crash the HTTP request if DB persist worked but workflow is gone/done
        # The manager's decision is recorded in DB regardless.

    return {"message": f"Application {status_msg}"}

@router.get("/applications/{application_id}/history")
async def get_application_history(
    application_id: str,
    current_user: User = Depends(deps.get_current_user)
):
    try:
        client = await temporal.get_client()
        handle = client.get_workflow_handle(application_id)

        # 1. Try Pyramid workflow logs first (CEO Workflow)
        try:
            worker_logs = await handle.query(LoanLifecycleWorkflow.get_logs)
            if worker_logs:
                return worker_logs
        except Exception:
            pass

        # 2. Try Original workflow logs
        try:
            worker_logs = await handle.query(LoanProcessWorkflow.get_logs)
            if worker_logs:
                return worker_logs
        except Exception:
            pass

        # 2. Fallback: Parse History Events (Legacy/Resilience)
        history = []
        async for event in handle.fetch_history_events():
            event_type = event.event_type
            timestamp = event.event_time.isoformat()
            
            # Narrative Mapping
            narrative = None
            agent_name = "System"
            
            if event_type == 1: # WorkflowExecutionStarted
                narrative = "Application received and workflow started."
                agent_name = "System"
                
            # Activity Tasks
            if hasattr(event, "activity_task_scheduled_event_attributes"):
                attrs = event.activity_task_scheduled_event_attributes
                act_type = attrs.activity_type.name
                
                if act_type == "init_loan_folder":
                    narrative = "Created secure folder structure for applicant documents."
                    agent_name = "Agent 0 (File Clerk)"
                elif act_type == "read_pdf_content":
                    narrative = "Extracted text content from uploaded PDF documents."
                    agent_name = "Agent 1 (OCR)"
                elif act_type == "analyze_document":
                    narrative = "Performed AI analysis to extract key financial data."
                    agent_name = "Agent 2 (Analyst)"
                elif act_type == "check_credit_score":
                    narrative = "Checked internal credit guidelines and risk logic."
                    agent_name = "Agent 3 (Risk)"
                
                if narrative:
                    history.append({
                        "agent": agent_name,
                        "message": narrative,
                        "timestamp": timestamp,
                        "original_type": act_type
                    })

            # Signals (Approve/Reject)
            elif hasattr(event, "workflow_execution_signaled_event_attributes"):
                 history.append({
                    "agent": "Agent 5 (Human Manager)",
                    "message": "Final Decision submitted via Dashboard.",
                    "timestamp": timestamp,
                    "original_type": "Signal"
                })

        return history

    except Exception as e:
        print(f"History Error: {e}")
        return []

@router.post("/applications/{workflow_id}/sign")
async def sign_documents(
    workflow_id: str,
    session: Session = Depends(deps.get_session),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Borrower signs the Initial Disclosures document.

    1. Locates the Initial Disclosures PDF
    2. Creates a signed copy: Initial Disclosures_SIGNED.pdf
    3. Signals the CEO Workflow with borrower_signature
    """
    import shutil

    # 1. Find the Initial Disclosures document
    app_dir = os.path.join(files.get_upload_root(), workflow_id)
    if not os.path.exists(app_dir):
        raise HTTPException(status_code=404, detail="Application files not found")

    # Look for Initial Disclosures PDF
    disclosure_path = None
    for filename in os.listdir(app_dir):
        if "Initial_Disclosures" in filename and filename.endswith(".pdf"):
            disclosure_path = os.path.join(app_dir, filename)
            break

    if not disclosure_path:
        raise HTTPException(
            status_code=404,
            detail="Initial Disclosures document not found. Please wait for processing to complete."
        )

    # 2. Create signed copy
    signed_filename = disclosure_path.replace(".pdf", "_SIGNED.pdf")
    shutil.copy2(disclosure_path, signed_filename)

    # 3. Update database
    app_record = session.exec(
        select(Application).where(Application.workflow_id == workflow_id)
    ).first()

    if app_record:
        app_record.status = "Documents Signed"
        session.add(app_record)
        session.commit()
    # 4. Signal Temporal Workflow
    try:
        client = await temporal.get_client()
        handle = client.get_workflow_handle(workflow_id)
        await handle.signal("borrower_signature", True)
    except Exception as e:
        print(f"Warning: Failed to signal workflow {workflow_id}: {e}")
        # DB update succeeded, workflow signal is best-effort

    return {
        "message": "Documents signed successfully",
        "workflow_id": workflow_id,
        "signed_document": f"/static/{workflow_id}/{os.path.basename(signed_filename)}"
    }


@router.delete("/application/{workflow_id}")
async def delete_application(workflow_id: str):
    client = await temporal.get_client()
    try:
        handle = client.get_workflow_handle(workflow_id)

        try:
            await handle.terminate("User requested deletion")
        except:
            pass

        files.delete_application_files(workflow_id)

        return {"status": "deleted", "workflow_id": workflow_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent_logs")
async def get_recent_logs(
    limit: int = 10,
    session: Session = Depends(deps.get_session),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get recent system logs across all active loan applications.
    Used for the Mission Control live activity stream.

    Returns aggregated logs from all running workflows, sorted by timestamp.
    """
    if current_user.role != "manager":
        raise HTTPException(status_code=403, detail="Only managers can view system logs")

    all_logs = []
    client = await temporal.get_client()

    # Get recent applications
    apps = session.query(Application).order_by(Application.created_at.desc()).limit(20).all()

    for app in apps:
        try:
            handle = client.get_workflow_handle(app.workflow_id)

            # Try to get logs from Pyramid workflow
            try:
                logs = await handle.query(LoanLifecycleWorkflow.get_logs)
                for log in logs[-5:]:  # Last 5 logs per workflow
                    all_logs.append({
                        **log,
                        "workflow_id": app.workflow_id,
                        "borrower": app.loan_metadata.get("applicant_info", {}).get("name", "Unknown") if app.loan_metadata else "Unknown"
                    })
            except Exception:
                pass

        except Exception:
            continue

    # Sort all logs by timestamp descending
    all_logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    return all_logs[:limit]


@router.get("/system_health")
async def get_system_health(
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get system health status for Mission Control dashboard.
    Shows status of AI Agent, DocGen, and Encompass workers.
    """
    if current_user.role != "manager":
        raise HTTPException(status_code=403, detail="Only managers can view system health")

    # Mock worker status - in production, check actual queue depth/worker health
    return {
        "workers": [
            {"name": "AI Analyst", "status": "online", "queue_depth": 0, "last_activity": "2s ago"},
            {"name": "DocGen MCP", "status": "online", "queue_depth": 0, "last_activity": "5s ago"},
            {"name": "Encompass MCP", "status": "online", "queue_depth": 0, "last_activity": "1s ago"},
            {"name": "Underwriting", "status": "online", "queue_depth": 0, "last_activity": "3s ago"},
        ],
        "temporal_connected": True,
        "database_connected": True
    }
