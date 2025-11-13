from pydantic import BaseModel
from typing import Literal
from datetime import datetime

class ExpenseCreate(BaseModel):
    employee_id: str
    amount: float
    category: str
    business_justification: str = ""

class ExpenseOut(BaseModel):
    expense_id: str
    status: Literal["pending", "approved", "rejected"] = "pending"
    submitted_at: datetime


class ExpenseUpdate(BaseModel):
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

    submitted_at: datetime
    updated_at: datetime
