from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AuditLogCreate(BaseModel):
    actor: str
    log: Optional[str] = ""

class AuditLogOut(AuditLogCreate):
    timestamp: datetime
