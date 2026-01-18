import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
import os 
# Import the code we wrote in previous steps
try:
    from activities import analyze_document, read_pdf_content, send_email_mock, organize_files
except ImportError:
    from .activities import analyze_document, read_pdf_content, send_email_mock, organize_files
from workflows import LoanProcessWorkflow

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
    worker = Worker(
        client,
        task_queue="loan-application-queue", # This is the channel name
        workflows=[LoanProcessWorkflow],
        activities=[analyze_document, read_pdf_content, send_email_mock, organize_files],
    )

    print("Worker started. Listening for tasks on 'loan-application-queue'...")
    
    # 3. Keep running indefinitely (until you stop the script)
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())