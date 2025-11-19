from fastapi import APIRouter
from domain.services import policy_service
from domain.schemas.policy_schema import PolicyCreate, PolicyUpdate, PolicyOut
from typing import List

router = APIRouter(prefix="/policies", tags=["Policy"])

@router.get("", response_model=List[PolicyOut])
def list_policies():
    return policy_service.list_policies()

@router.post("", response_model=PolicyOut)
def create_policy(data: PolicyCreate):
    return policy_service.create_policy(data.dict())

@router.patch("/{policy_id}", response_model=PolicyOut)
def update_policy(policy_id: str, data: PolicyUpdate):
    return policy_service.update_policy(policy_id, data.dict(exclude_unset=True))

@router.delete("/{policy_id}")
def delete_policy(policy_id: str):
    return policy_service.delete_policy(policy_id)
