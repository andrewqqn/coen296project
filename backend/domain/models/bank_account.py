from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Literal

@dataclass
class BankAccount:
    bank_account_id: str
    holder_name: str = None
    email: str = None
    employee_id: str = None
    balance: float = 0.0
    
    def __post_init__(self):
        """Ensure balance has 2 decimal precision"""
        if self.balance is not None:
            self.balance = round(float(self.balance), 2)