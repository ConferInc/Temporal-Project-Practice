from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    email: str
    password: str
    initial_metadata: Optional[dict] = None  # Moxi Portal: Funnel answers from borrower flow


class ApprovalRequest(BaseModel):
    workflow_id: str
    approved: bool
    reason: Optional[str] = None


# =========================================
# Pyramid Architecture: Signal Models
# =========================================

class SignalApprove(BaseModel):
    """Signal payload for approving a loan stage"""
    workflow_id: str
    approved_by: Optional[str] = None


class SignalReject(BaseModel):
    """Signal payload for rejecting a loan with reason"""
    workflow_id: str
    reason: str
    rejected_by: Optional[str] = None
