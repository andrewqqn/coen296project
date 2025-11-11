from fastapi import APIRouter, HTTPException
from domain.services import employee_service
router = APIRouter(prefix="/employees", tags=["Employee"])
@router.get("")
def list_employee():
    return employee_service.list_employees()
@router.get("/{employee_id}")
def get_employee(employee_id: str):
    try:
        return employee_service.get_employee(employee_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Employee not found")
@router.post("")
def create_employee(data: dict):
    return employee_service.create_employee(data)
@router.patch("/{employee_id}")
def update_employee(employee_id: str, data: dict):
    return employee_service.update_employee(employee_id, data)
@router.delete("/{employee_id}")
def delete_employee(employee_id: str):
    return employee_service.delete_employee(employee_id)
