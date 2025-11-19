from pydantic import BaseModel
from typing import Literal
from datetime import datetime

class ExpenseCreate(BaseModel):
    date_of_expense: datetime
    employee_id: str
    amount: float
    business_justification: str
    category: Literal["Travel", "Meals", "Conference", "Other"] = "Other"


class ExpenseOut(BaseModel):
    expense_id: str
    date_of_expense: datetime

    employee_id: str
    amount: float
    business_justification: str
    category: Literal["Travel", "Meals", "Conference", "Other"] = "Other"

    status: Literal["pending", "approved", "rejected", "admin-review"] = "pending"
    decision_actor: str = None
    decision_reason: str = None

    receipt_path: str

    submitted_at: datetime
    updated_at: datetime


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
