"""
Production-Grade Loan Application Schema

This module defines the LoanApplication SQLModel with strict schema philosophy
to support the Waiter Pattern and underwriting workflow.
"""
import uuid
from typing import Optional
from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel
from sqlalchemy import Column, JSON, Text


class UnderwritingStatus(str, Enum):
    """Status values for underwriting decision (Waiter Pattern)"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class LoanStatus(str, Enum):
    """Overall loan application status"""
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    PENDING_UNDERWRITING = "pending_underwriting"
    UNDERWRITING_COMPLETE = "underwriting_complete"
    CLOSING = "closing"
    FUNDED = "funded"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class LoanApplication(SQLModel, table=True):
    """
    Production-grade Loan Application model.

    This schema supports the Waiter Pattern workflow with explicit state tracking
    for underwriting decisions and workflow synchronization.

    Table name: loanapplication (SQLModel default from class name)
    """
    __tablename__ = "loan_application"

    # Primary Key: UUID for distributed systems compatibility
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        description="Unique identifier for the loan application"
    )

    # Temporal Workflow Link
    workflow_id: str = Field(
        index=True,
        unique=True,
        description="Links to the Temporal workflow orchestrating this application"
    )

    # Borrower Information
    borrower_name: str = Field(
        description="Full legal name of the primary borrower"
    )
    borrower_email: Optional[str] = Field(
        default=None,
        description="Contact email for the borrower"
    )

    # Loan Details
    loan_amount: float = Field(
        default=0.0,
        description="Requested loan amount in USD"
    )
    property_value: Optional[float] = Field(
        default=None,
        description="Appraised or estimated property value"
    )
    down_payment: Optional[float] = Field(
        default=None,
        description="Down payment amount"
    )

    # Application Status
    status: str = Field(
        default=LoanStatus.SUBMITTED.value,
        description="Current status of the loan application"
    )
    loan_stage: Optional[str] = Field(
        default=None,
        description="Current stage in the Pyramid Architecture workflow"
    )

    # =========================================
    # Waiter Pattern State
    # =========================================
    is_locked: bool = Field(
        default=False,
        description="Lock flag for Waiter Pattern - prevents concurrent modifications"
    )
    underwriting_decision: Optional[str] = Field(
        default=None,
        description="Human underwriting decision: approved, rejected, or null if pending"
    )
    underwriting_decision_reason: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Reason provided by underwriter for their decision"
    )
    underwriting_decided_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when underwriting decision was made"
    )
    underwriting_decided_by: Optional[str] = Field(
        default=None,
        description="ID or email of the underwriter who made the decision"
    )

    # Automated Underwriting Results
    automated_uw_decision: Optional[str] = Field(
        default=None,
        description="Result from automated UnderwritingWorkflow"
    )
    risk_score: Optional[float] = Field(
        default=None,
        description="Calculated risk score from automated underwriting"
    )

    # AI Analysis Results (stored as JSON for flexibility)
    ai_analysis: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON),
        description="AI document analysis results including income verification"
    )

    # Encompass Integration
    loan_number: Optional[str] = Field(
        default=None,
        index=True,
        description="Loan number from Encompass LOS"
    )

    # Audit Trail
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when application was created"
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp of last update"
    )

    # Flexible Metadata (for future extensions)
    application_metadata: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Additional metadata that doesn't fit structured fields"
    )

    class Config:
        """Pydantic/SQLModel configuration"""
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "workflow_id": "loan-alice-12345",
                "borrower_name": "Alice Johnson",
                "borrower_email": "alice@example.com",
                "loan_amount": 450000.00,
                "status": "pending_underwriting",
                "is_locked": False,
                "underwriting_decision": None,
                "created_at": "2024-01-15T10:30:00Z"
            }
        }


# =========================================
# Helper Functions for Waiter Pattern
# =========================================

def lock_application(session, workflow_id: str) -> bool:
    """
    Acquire a lock on the application for the Waiter Pattern.
    Returns True if lock was acquired, False if already locked.
    """
    app = session.query(LoanApplication).filter(
        LoanApplication.workflow_id == workflow_id
    ).first()

    if app and not app.is_locked:
        app.is_locked = True
        app.updated_at = datetime.utcnow()
        session.commit()
        return True
    return False


def unlock_application(session, workflow_id: str) -> bool:
    """
    Release the lock on the application after Waiter Pattern completes.
    """
    app = session.query(LoanApplication).filter(
        LoanApplication.workflow_id == workflow_id
    ).first()

    if app:
        app.is_locked = False
        app.updated_at = datetime.utcnow()
        session.commit()
        return True
    return False


def record_underwriting_decision(
    session,
    workflow_id: str,
    decision: str,
    reason: str,
    decided_by: Optional[str] = None
) -> Optional[LoanApplication]:
    """
    Record the underwriting decision in the database (Waiter Pattern).

    Args:
        session: Database session
        workflow_id: The Temporal workflow ID
        decision: "approved" or "rejected"
        reason: Explanation for the decision
        decided_by: Optional identifier of the underwriter

    Returns:
        Updated LoanApplication or None if not found
    """
    app = session.query(LoanApplication).filter(
        LoanApplication.workflow_id == workflow_id
    ).first()

    if app:
        app.underwriting_decision = decision
        app.underwriting_decision_reason = reason
        app.underwriting_decided_at = datetime.utcnow()
        app.underwriting_decided_by = decided_by
        app.updated_at = datetime.utcnow()

        # Update status based on decision
        if decision == UnderwritingStatus.APPROVED.value:
            app.status = LoanStatus.UNDERWRITING_COMPLETE.value
        elif decision == UnderwritingStatus.REJECTED.value:
            app.status = LoanStatus.REJECTED.value

        session.commit()
        session.refresh(app)
        return app

    return None
