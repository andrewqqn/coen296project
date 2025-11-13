from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Literal

@dataclass
class BankAccount:
    holder_name: str = None
    bank_account: str = None
    email: str = None
    notes: Optional[str] = None