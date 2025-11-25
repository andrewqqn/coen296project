from fastapi import APIRouter
from services import audit_log_service
from domain.schemas.audit_schema import AuditLogCreate, AuditLogOut
from typing import List

router = APIRouter(prefix="/audit_logs", tags=["AuditLog"])

@router.get("", response_model=List[AuditLogOut])
def list_logs():
    return audit_log_service.list_logs()

@router.post("", response_model=AuditLogOut)
def create_log(data: AuditLogCreate):
    return audit_log_service.create_log(data.model_dump())
