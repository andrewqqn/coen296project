from dataclasses import dataclass, field
from typing import Literal, Optional, Dict

@dataclass
class ReimbursementPolicy:
    policy_id: Optional[str] = None                 # Firestore generated ID
    category: str = ""                              # e.g. "Travel", "Meal", "Office"
    max_amount: float = 0.0                         # single-time maxi amount
    eligible_roles: list[str] = field(default_factory=lambda: ["employee"])
    description: Optional[str] = None
    active: bool = True
