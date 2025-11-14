from pydantic import BaseModel, EmailStr
from typing import Optional, Literal

class EmployeeCreate(BaseModel):
    authentication_id: str
    email: str
    name: str
    position: str
    role: Literal["employee", "admin"] = "employee"
    bank_account: Optional[str] = None
    notes: Optional[str] = None

class EmployeeUpdate(EmployeeCreate):
    pass

class EmployeeOut(EmployeeCreate):
    employee_id: str
