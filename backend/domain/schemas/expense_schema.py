from pydantic import BaseModel, HttpUrl
from typing import Optional, Literal
from datetime import datetime

class ExpenseCreate(BaseModel):
    employee_id: str
    amount: float
    category: str
    description: str = ""
    receipt_url: Optional[HttpUrl] = None

class ExpenseUpdate(BaseModel):
    amount: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Literal["pending", "approved", "rejected"]] = None
    decision_reason: Optional[str] = None

class ExpenseOut(BaseModel):
    expense_id: str
    status: Literal["pending", "approved", "rejected"]
    decision_type: Literal["AI", "Human"]
    reviewed_by: Optional[str] = None
    decision_reason: Optional[str] = None
    submitted_at: datetime
    updated_at: datetime
