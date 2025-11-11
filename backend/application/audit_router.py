from fastapi import APIRouter
from domain.services import audit_service
router = APIRouter(prefix="/audit_logs", tags=["AuditLog"])
@router.get("")
def list_logs():
    return audit_service.list_logs()
@router.post("")
def create_log(data: dict):
    return audit_service.create_log(data)
