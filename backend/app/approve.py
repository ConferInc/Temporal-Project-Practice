import asyncio
from temporalio.client import Client

# We import the workflow definition to ensure we use the correct Signal name
from workflows import LoanProcessWorkflow

async def main():
    # 1. Connect to Temporal 
    # IMPORTANT: Make sure this matches the port in your worker.py (likely 8888 or 7233)
    client = await Client.connect("localhost:8888")

    print("Sending approval signal...")

    # 2. Get a handle to the specific workflow running right now
    # This ID must match what you used in starter.py
    workflow_id = "loan-application-1"
    
    handle = client.get_workflow_handle(workflow_id)

    # 3. Send the signal!
    # True = Approved, False = Rejected
    await handle.signal(LoanProcessWorkflow.is_waiting, True)

    print(f"Signal sent to {workflow_id}: Loan Approved!")

if __name__ == "__main__":
    asyncio.run(main())