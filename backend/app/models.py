from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel, JSON
from sqlalchemy import Column # Needed for JSON column type

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    role: str = Field(default="applicant") # "applicant" or "manager"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Application(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    
    # Workflow Metadata
    workflow_id: str = Field(index=True, unique=True)
    status: str = Field(default="Submitted")
    
    # Loan Details
    loan_amount: float = Field(default=0.0)
    
    # Flexible Metadata (Documents, Income, etc.)
    # We use sa_column for JSON/JSONB types to store complex structures
    loan_metadata: dict = Field(default={}, sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
