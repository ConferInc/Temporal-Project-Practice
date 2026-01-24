from typing import Optional
from datetime import datetime
from enum import Enum
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, JSON, Enum as SAEnum


class LoanStage(str, Enum):
    """The 5 stages of the Moxi Corp Loan Lifecycle Pyramid"""
    LEAD_CAPTURE = "LEAD_CAPTURE"
    PROCESSING = "PROCESSING"
    UNDERWRITING = "UNDERWRITING"
    CLOSING = "CLOSING"
    ARCHIVED = "ARCHIVED"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    role: str = Field(default="applicant")  # "applicant" or "manager"

    # Moxi Portal: Funnel data from borrower registration flow
    initial_metadata: Optional[dict] = Field(default=None, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=datetime.utcnow)

class Application(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Relationships
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")

    # Workflow Metadata
    workflow_id: str = Field(index=True, unique=True)
    status: str = Field(default="Submitted")

    # Pyramid Architecture: Loan Stage Tracking (None for original workflow)
    loan_stage: Optional[str] = Field(default=None)

    # Loan Details
    loan_amount: float = Field(default=0.0)

    # Flexible Metadata (Documents, Income, etc.)
    # We use sa_column for JSON/JSONB types to store complex structures
    loan_metadata: dict = Field(default={}, sa_column=Column(JSON))
    decision_reason: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow)
