from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Literal

@dataclass
class AuditLog:
    actor: str
    action: Literal["create", "update", "delete"]
    target_type: Literal["expense", "employee", "policy"]
    target_id: Optional[str] = None
    log_notes: str = ""
    action_type: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
