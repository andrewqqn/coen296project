from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Literal

@dataclass
class Expense:
    expense_id: Optional[str] = None          # Firestore generated ID
    employee_id: str = ""
    amount: float = 0.0
    category: str = ""
    description: str = ""
    receipt_url: Optional[str] = None         # Firebase Storage path

    status: Literal["pending", "approved", "rejected"] = "pending"
    decision_type: Literal["AI", "Human"] = "AI"
    reviewed_by: Optional[str] = None
    decision_reason: Optional[str] = None

    submitted_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
