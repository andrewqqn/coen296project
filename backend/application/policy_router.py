from fastapi import APIRouter, HTTPException
from infrastructure.auth_middleware import verify_firebase_token
from domain.services import policy_service
router = APIRouter(prefix="/policies", tags=["Policy"])
@router.get("")
def list_policies():
    return policy_service.list_policies()
@router.post("")
def create_policy(data: dict):
    return policy_service.create_policy(data)
@router.patch("/{policy_id}")
def update_policy(policy_id: str, data: dict):
    return policy_service.update_policy(policy_id, data)
@router.delete("/{policy_id}")
def delete_policy(policy_id: str):
    return policy_service.delete_policy(policy_id)
