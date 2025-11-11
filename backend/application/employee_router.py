from fastapi import APIRouter, HTTPException
from domain.services import employee_service
from domain.schemas.employee_schema import EmployeeCreate, EmployeeUpdate, EmployeeOut
from typing import List

router = APIRouter(prefix="/employees", tags=["Employee"])

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
    return employee_service.create_employee(data.dict())

@router.patch("/{employee_id}", response_model=EmployeeOut)
def update_employee(employee_id: str, data: EmployeeUpdate):
    return employee_service.update_employee(employee_id, data.dict(exclude_unset=True))

@router.delete("/{employee_id}")
def delete_employee(employee_id: str):
    return employee_service.delete_employee(employee_id)
