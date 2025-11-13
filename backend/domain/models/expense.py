from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Literal

@dataclass
class Expense:
    expense_id: str
    date_of_expense: datetime

    employee_id: str
    amount: float
    business_justification: str
    category: Literal["Travel", "Meals", "Conference", "Other"] = "Other"

    status: Literal["pending", "approved", "rejected"] = "pending"
    decision_actor: Literal["AI", "Human"] = "AI"
    decision_reason: str = None

    receipt_path: str = None         # Firebase Storage path

    submitted_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
