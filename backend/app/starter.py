import asyncio
import sys
from temporalio.client import Client

# Import the Workflow definition so we can use it simply as a reference
from workflows import LoanProcessWorkflow

async def main():
    # 1. Connect to Temporal
    client = await Client.connect("localhost:8888")

    # 2. Simulate a Document (Pass this as a command line argument or use default)
    # This text mimics a messy file read by OCR
    mock_document = "Applicant: John Doe.  Annual Income: $45,000. Credit Score: 650."
    
    # 3. Start the Workflow
    # We give it an ID 'loan-application-1' so we can find it easily in the UI.
    handle = await client.start_workflow(
        LoanProcessWorkflow.run,
        mock_document,
        id="loan-application-1",
        task_queue="loan-application-queue",
    )

    print(f"Workflow started successfully! ID: {handle.id}")
    print(f"Run ID: {handle.result_run_id}")
    print("Go to http://localhost:8233 to see it running.")

    # Optional: Wait for result (This will hang if the workflow pauses for human input)
    # result = await handle.result()
    # print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())