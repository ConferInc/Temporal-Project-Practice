"""
Pyramid Architecture: Level 3 - Encompass MCP Worker

The EncompassMCP handles all Loan Origination System (LOS) operations:
- Creating loan files in Encompass
- Pushing field updates
- Syncing loan data
- Updating loan metadata in SQL

This is a mock implementation with print logs for development.
In production, integrate with Encompass API via ICE Mortgage Technology SDK.
"""
from dataclasses import dataclass
from temporalio import activity
from datetime import datetime
import uuid

# Database imports for update_loan_metadata activity
from sqlmodel import Session, select
from app.core.database import engine
from app.models.sql import Application


@dataclass
class EncompassMCP:
    """Encompass MCP - handles LOS operations"""

    @staticmethod
    def create_loan_file(data: dict) -> dict:
        """
        Create a new loan file in Encompass LOS.

        Args:
            data: Loan application data including applicant info

        Returns:
            Dict with loan_number and status
        """
        timestamp = datetime.utcnow().isoformat()
        # Generate a mock Encompass loan number
        loan_number = f"ENC-{uuid.uuid4().hex[:8].upper()}"

        print(f"[EncompassMCP] [{timestamp}] LOAN FILE CREATED")
        print(f"  Loan Number: {loan_number}")
        print(f"  Applicant: {data.get('applicant_name', 'Unknown')}")
        print(f"  Data Keys: {list(data.keys())}")

        return {
            "loan_number": loan_number,
            "status": "Created",
            "created_at": timestamp
        }

    @staticmethod
    def push_field_update(loan_number: str, field_id: str, value: str) -> str:
        """
        Push a field update to an existing loan file.

        Args:
            loan_number: Encompass loan number
            field_id: Field identifier (e.g., "CX.LOAN_STAGE", "4000")
            value: New field value

        Returns:
            Status message
        """
        timestamp = datetime.utcnow().isoformat()
        print(f"[EncompassMCP] [{timestamp}] FIELD UPDATE")
        print(f"  Loan: {loan_number}")
        print(f"  Field: {field_id} = {value}")

        return f"Field {field_id} updated to '{value}' for loan {loan_number}"


# =========================================
# Temporal Activity Functions
# =========================================

@activity.defn
async def create_loan_file(data: dict) -> dict:
    """Temporal Activity: Create loan file via EncompassMCP"""
    return EncompassMCP.create_loan_file(data)


@activity.defn
async def push_field_update(loan_number: str, field_id: str, value: str) -> str:
    """Temporal Activity: Push field update via EncompassMCP"""
    return EncompassMCP.push_field_update(loan_number, field_id, value)


@activity.defn
async def update_loan_metadata(workflow_id: str, metadata_update: dict) -> dict:
    """
    Temporal Activity: Update loan_metadata in SQL database.

    This activity persists AI analysis results and other workflow data
    to the Application SQL record so the frontend can display it.

    IMPORTANT: Special keys are extracted and written to SQL columns directly:
    - "status" -> Application.status column
    - "loan_stage" -> Application.loan_stage column
    All other keys go into the loan_metadata JSON field.

    Args:
        workflow_id: The workflow/application ID
        metadata_update: Dict of fields to merge into loan_metadata

    Returns:
        Dict with status and updated fields
    """
    timestamp = datetime.utcnow().isoformat()
    print(f"[EncompassMCP] [{timestamp}] UPDATE LOAN METADATA")
    print(f"  Workflow ID: {workflow_id}")
    print(f"  Update Keys: {list(metadata_update.keys())}")

    try:
        with Session(engine) as session:
            app_record = session.exec(
                select(Application).where(Application.workflow_id == workflow_id)
            ).first()

            if not app_record:
                return {
                    "status": "error",
                    "message": f"Application not found: {workflow_id}"
                }

            # Extract special SQL column fields from metadata_update
            sql_status = metadata_update.pop("status", None)
            sql_loan_stage = metadata_update.pop("loan_stage", None)

            # Update SQL columns directly if provided
            if sql_status:
                app_record.status = sql_status
                print(f"  [SQL Column] status = {sql_status}")

            if sql_loan_stage:
                app_record.loan_stage = sql_loan_stage
                print(f"  [SQL Column] loan_stage = {sql_loan_stage}")

            # Merge remaining data into existing loan_metadata JSON
            current_metadata = app_record.loan_metadata or {}
            current_metadata.update(metadata_update)
            app_record.loan_metadata = current_metadata

            session.add(app_record)
            session.commit()

            print(f"[EncompassMCP] [{timestamp}] METADATA UPDATED SUCCESSFULLY")
            return {
                "status": "success",
                "workflow_id": workflow_id,
                "updated_keys": list(metadata_update.keys()),
                "sql_status": sql_status,
                "sql_loan_stage": sql_loan_stage
            }
    except Exception as e:
        print(f"[EncompassMCP] [{timestamp}] ERROR: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
