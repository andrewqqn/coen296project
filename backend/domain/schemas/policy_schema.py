from pydantic import BaseModel
from typing import Optional, List

class PolicyCreate(BaseModel):
    category: str
    max_amount: float
    eligible_roles: List[str] = ["employee"]
    description: Optional[str] = None
    active: bool = True

class PolicyUpdate(BaseModel):
    max_amount: Optional[float] = None
    eligible_roles: Optional[List[str]] = None
    description: Optional[str] = None
    active: Optional[bool] = None

class PolicyOut(PolicyCreate):
    policy_id: str
