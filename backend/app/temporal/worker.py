import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
import os

# Original workflow and activities
from app.temporal.activities import analyze_document, read_pdf_content, send_email_mock, organize_files
from app.temporal.workflows import LoanProcessWorkflow

# Pyramid Architecture: New Workflows (Level 1 & 2)
from app.temporal.workflows.ceo import LoanLifecycleWorkflow
from app.temporal.workflows.managers import LeadCaptureWorkflow, ProcessingWorkflow

# Pyramid Architecture: New Activities (Level 3 - MCP Workers)
from app.temporal.activities.mcp_comms import send_email, send_sms
from app.temporal.activities.mcp_encompass import create_loan_file, push_field_update
from app.temporal.activities.mcp_docgen import generate_document

async def main():
    # 1. Connect to the Temporal Server
    # 'localhost:7233' assumes you are running Temporal locally (e.g., via Docker).
    # If you deploy this to Coolify later, you will change this to your VPS address.
    
    temporal_url = os.getenv("TEMPORAL_HOST", "localhost:7233")
    while True:
        try:
            client = await Client.connect(temporal_url)
            print(f"Successfully connected to Temporal at {temporal_url}")
            break
        except Exception as e:
            print(f"Failed to connect to Temporal at {temporal_url}, retrying in 5 seconds... Error: {e}")
            await asyncio.sleep(5)

    # 2. Create the Worker
    # We tell it which "Queue" to listen to, and which functions it is allowed to run.
    # Pyramid Architecture: Register all workflow levels and MCP activities
    worker = Worker(
        client,
        task_queue="loan-application-queue",
        workflows=[
            # Original workflow (maintained for backward compatibility)
            LoanProcessWorkflow,
            # Pyramid Architecture Workflows
            LoanLifecycleWorkflow,    # Level 1: CEO
            LeadCaptureWorkflow,      # Level 2: Manager
            ProcessingWorkflow,       # Level 2: Manager
        ],
        activities=[
            # Original activities
            analyze_document,
            read_pdf_content,
            send_email_mock,
            organize_files,
            # Pyramid Architecture: MCP Workers (Level 3)
            send_email,
            send_sms,
            create_loan_file,
            push_field_update,
            generate_document,
        ],
    )

    print("Worker started. Listening for tasks on 'loan-application-queue'...")
    
    # 3. Keep running indefinitely (until you stop the script)
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())