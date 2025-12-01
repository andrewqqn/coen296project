from fastapi import APIRouter, HTTPException, Depends
from services import employee_service
from domain.schemas.employee_schema import EmployeeCreate, EmployeeUpdate, EmployeeOut
from typing import List
from utils.auth import get_current_user

router = APIRouter(prefix="/employees", tags=["Employee"])

@router.get("/me", response_model=EmployeeOut)
def get_current_employee(current_user: dict = Depends(get_current_user)):
    """Get the current authenticated user's employee profile"""
    emp = employee_service.get_employee_by_auth_id(current_user["uid"])
    if emp is None:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    return emp

@router.get("", response_model=List[EmployeeOut])
def list_employee():
    return employee_service.list_employees()

@router.get("/{employee_id}", response_model=EmployeeOut)
def get_employee(employee_id: str):
    emp = employee_service.get_employee(employee_id)
    if emp is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp

@router.post("", response_model=EmployeeOut)
def create_employee(data: EmployeeCreate):
    return employee_service.create_employee(data.model_dump())

@router.patch("/{employee_id}", response_model=EmployeeOut)
def update_employee(employee_id: str, data: EmployeeUpdate):
    return employee_service.update_employee(employee_id, data.model_dump(exclude_unset=True))

@router.delete("/{employee_id}")
def delete_employee(employee_id: str):
    return employee_service.delete_employee(employee_id)
