from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    email: str
    password: str

class ApprovalRequest(BaseModel):
    workflow_id: str
    approved: bool
    reason: Optional[str] = None
