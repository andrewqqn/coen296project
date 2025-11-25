from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Literal

@dataclass
class Employee:
    authentication_id: str
    employee_id: str
    email: str
    name: str

    position: str
    role: Literal["employee", "admin"] = "employee"

    bank_account: Optional[str] = None

    notes: Optional[str] = None
