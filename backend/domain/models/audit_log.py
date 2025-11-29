from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Literal

@dataclass
class AuditLog:
    actor: Literal["AI", "Human"]
    log: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
