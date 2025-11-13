from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Literal

@dataclass
class AuditLog:
    actor: str
    log: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
