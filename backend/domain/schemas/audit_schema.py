from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

class AuditLogCreate(BaseModel):
    actor: str
    action: Literal["create", "update", "delete"]
    target_type: Literal["expense", "employee", "policy"]
    target_id: Optional[str] = None
    log_notes: Optional[str] = ""
    action_type: Optional[str] = ""

class AuditLogOut(AuditLogCreate):
    timestamp: datetime
