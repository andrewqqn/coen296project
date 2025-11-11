from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Literal

@dataclass
class Employee:
    email: str

    uid: str
    name: str
    position: str
    department: str

    manager_id: Optional[str] = None
    role: Literal["employee", "admin"] = "employee"

    bank_account: Optional[str] = None

    notes: Optional[str] = None
