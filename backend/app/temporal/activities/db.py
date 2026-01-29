"""
Database Activities for Temporal Workflows

These activities provide the "wiring" between Temporal workflows and the
PostgreSQL database using the LoanApplication model.

Key Activities:
- init_loan_record: Creates initial DB record when workflow starts
- update_loan_status: Updates status/stage during workflow progression
- save_underwriting_decision: Records human underwriting decisions (Waiter Pattern)
"""
from datetime import datetime
from typing import Optional
from temporalio import activity

from app.database import get_session_context
from app.models.application import (
    LoanApplication,
    LoanStatus,
    UnderwritingStatus,
)


@activity.defn
async def init_loan_record(
    workflow_id: str,
    borrower_name: str,
    borrower_email: str,
    loan_amount: float,
    property_value: float = 0.0,
    down_payment: float = 0.0
) -> str:
    """
    Initialize a LoanApplication record in Postgres when workflow starts.

    Args:
        workflow_id: The Temporal workflow ID
        borrower_name: Full name of the borrower
        borrower_email: Borrower's email address
        loan_amount: Requested loan amount
        property_value: Property value (optional)
        down_payment: Down payment amount (optional)

    Returns:
        str: The UUID of the created record
    """
    activity.logger.info(f"Creating loan record for workflow: {workflow_id}")

    with get_session_context() as session:
        # Check if record already exists (idempotency)
        existing = session.query(LoanApplication).filter(
            LoanApplication.workflow_id == workflow_id
        ).first()

        if existing:
            activity.logger.info(f"Loan record already exists: {existing.id}")
            return str(existing.id)

        # Create new record
        loan_app = LoanApplication(
            workflow_id=workflow_id,
            borrower_name=borrower_name,
            borrower_email=borrower_email,
            loan_amount=loan_amount,
            property_value=property_value,
            down_payment=down_payment,
            status=LoanStatus.SUBMITTED.value,
            loan_stage="LEAD_CAPTURE",
            is_locked=False,
            created_at=datetime.utcnow()
        )

        session.add(loan_app)
        session.commit()
        session.refresh(loan_app)

        activity.logger.info(f"Created loan record with ID: {loan_app.id}")
        return str(loan_app.id)


@activity.defn
async def update_loan_status(
    workflow_id: str,
    status: str,
    stage: str,
    is_locked: bool = False,
    additional_data: Optional[dict] = None
) -> bool:
    """
    Update the status and stage of a loan application.

    Args:
        workflow_id: The Temporal workflow ID
        status: New status value (e.g., "Processing", "Pending Underwriting")
        stage: Current loan stage (e.g., "PROCESSING", "UNDERWRITING")
        is_locked: Set to True when entering a wait state (Waiter Pattern)
        additional_data: Optional dict with extra fields to update

    Returns:
        bool: True if update succeeded
    """
    activity.logger.info(f"Updating loan status: {workflow_id} -> {status} ({stage}), locked={is_locked}")

    with get_session_context() as session:
        loan_app = session.query(LoanApplication).filter(
            LoanApplication.workflow_id == workflow_id
        ).first()

        if not loan_app:
            activity.logger.warning(f"Loan record not found: {workflow_id}")
            return False

        # Update core fields
        loan_app.status = status
        loan_app.loan_stage = stage
        loan_app.is_locked = is_locked
        loan_app.updated_at = datetime.utcnow()

        # Update additional fields if provided
        if additional_data:
            for key, value in additional_data.items():
                if hasattr(loan_app, key):
                    setattr(loan_app, key, value)

        session.commit()
        activity.logger.info(f"Updated loan record: {loan_app.id}")
        return True


@activity.defn
async def save_underwriting_decision(
    workflow_id: str,
    decision: str,
    reason: str,
    decided_by: Optional[str] = None
) -> bool:
    """
    Save the human underwriting decision to the database (Waiter Pattern).

    This activity is called after the workflow receives the underwriting
    decision signal, to persist the decision to Postgres.

    Args:
        workflow_id: The Temporal workflow ID
        decision: "approved" or "rejected"
        reason: Explanation for the decision
        decided_by: Optional identifier of the underwriter

    Returns:
        bool: True if update succeeded
    """
    activity.logger.info(f"Saving underwriting decision: {workflow_id} -> {decision}")

    with get_session_context() as session:
        loan_app = session.query(LoanApplication).filter(
            LoanApplication.workflow_id == workflow_id
        ).first()

        if not loan_app:
            activity.logger.warning(f"Loan record not found: {workflow_id}")
            return False

        # Update underwriting decision fields
        loan_app.underwriting_decision = decision
        loan_app.underwriting_decision_reason = reason
        loan_app.underwriting_decided_at = datetime.utcnow()
        loan_app.underwriting_decided_by = decided_by
        loan_app.updated_at = datetime.utcnow()

        # Update status based on decision
        if decision == UnderwritingStatus.APPROVED.value:
            loan_app.status = LoanStatus.UNDERWRITING_COMPLETE.value
            loan_app.is_locked = False  # Unlock after decision
        elif decision == UnderwritingStatus.REJECTED.value:
            loan_app.status = LoanStatus.REJECTED.value
            loan_app.is_locked = False
        elif decision == UnderwritingStatus.WITHDRAWN.value:
            loan_app.status = LoanStatus.WITHDRAWN.value
            loan_app.is_locked = False

        session.commit()
        activity.logger.info(f"Saved underwriting decision for: {loan_app.id}")
        return True


@activity.defn
async def update_loan_ai_analysis(
    workflow_id: str,
    analysis_data: dict
) -> bool:
    """
    Update the AI analysis results for a loan application.

    Args:
        workflow_id: The Temporal workflow ID
        analysis_data: Dict containing AI analysis results

    Returns:
        bool: True if update succeeded
    """
    activity.logger.info(f"Updating AI analysis for: {workflow_id}")

    with get_session_context() as session:
        loan_app = session.query(LoanApplication).filter(
            LoanApplication.workflow_id == workflow_id
        ).first()

        if not loan_app:
            activity.logger.warning(f"Loan record not found: {workflow_id}")
            return False

        loan_app.ai_analysis = analysis_data
        loan_app.updated_at = datetime.utcnow()

        session.commit()
        return True


@activity.defn
async def update_automated_underwriting(
    workflow_id: str,
    decision: str,
    risk_score: Optional[float] = None,
    risk_evaluation: Optional[dict] = None
) -> bool:
    """
    Update the automated underwriting results from UnderwritingWorkflow.

    Args:
        workflow_id: The Temporal workflow ID
        decision: Automated decision (e.g., "CLEAR_TO_CLOSE", "REFER_TO_HUMAN")
        risk_score: Optional calculated risk score
        risk_evaluation: Optional detailed risk evaluation

    Returns:
        bool: True if update succeeded
    """
    activity.logger.info(f"Updating automated underwriting: {workflow_id} -> {decision}")

    with get_session_context() as session:
        loan_app = session.query(LoanApplication).filter(
            LoanApplication.workflow_id == workflow_id
        ).first()

        if not loan_app:
            activity.logger.warning(f"Loan record not found: {workflow_id}")
            return False

        loan_app.automated_uw_decision = decision
        if risk_score is not None:
            loan_app.risk_score = risk_score
        loan_app.updated_at = datetime.utcnow()

        # Store risk evaluation in application_metadata if provided
        if risk_evaluation:
            if loan_app.application_metadata is None:
                loan_app.application_metadata = {}
            loan_app.application_metadata["risk_evaluation"] = risk_evaluation

        session.commit()
        return True


@activity.defn
async def finalize_loan_record(
    workflow_id: str,
    final_status: str,
    final_stage: str
) -> bool:
    """
    Finalize the loan record when workflow completes.

    Args:
        workflow_id: The Temporal workflow ID
        final_status: Final status (e.g., "Funded", "Rejected")
        final_stage: Final stage (e.g., "ARCHIVED")

    Returns:
        bool: True if update succeeded
    """
    activity.logger.info(f"Finalizing loan record: {workflow_id} -> {final_status}")

    with get_session_context() as session:
        loan_app = session.query(LoanApplication).filter(
            LoanApplication.workflow_id == workflow_id
        ).first()

        if not loan_app:
            activity.logger.warning(f"Loan record not found: {workflow_id}")
            return False

        loan_app.status = final_status
        loan_app.loan_stage = final_stage
        loan_app.is_locked = False
        loan_app.updated_at = datetime.utcnow()

        session.commit()
        activity.logger.info(f"Finalized loan record: {loan_app.id}")
        return True


@activity.defn
async def get_loan_record(workflow_id: str) -> Optional[dict]:
    """
    Retrieve the loan record for a workflow.

    Args:
        workflow_id: The Temporal workflow ID

    Returns:
        dict: The loan record data or None if not found
    """
    with get_session_context() as session:
        loan_app = session.query(LoanApplication).filter(
            LoanApplication.workflow_id == workflow_id
        ).first()

        if not loan_app:
            return None

        return {
            "id": str(loan_app.id),
            "workflow_id": loan_app.workflow_id,
            "borrower_name": loan_app.borrower_name,
            "borrower_email": loan_app.borrower_email,
            "loan_amount": loan_app.loan_amount,
            "status": loan_app.status,
            "loan_stage": loan_app.loan_stage,
            "is_locked": loan_app.is_locked,
            "underwriting_decision": loan_app.underwriting_decision,
            "underwriting_decision_reason": loan_app.underwriting_decision_reason,
            "automated_uw_decision": loan_app.automated_uw_decision,
            "created_at": loan_app.created_at.isoformat() if loan_app.created_at else None,
            "updated_at": loan_app.updated_at.isoformat() if loan_app.updated_at else None,
        }
