from fastapi import APIRouter, HTTPException, Depends
from services import expense_service, employee_service
from domain.schemas.expense_schema import (ExpenseCreate, ExpenseOut, ExpenseUpdate)
from fastapi import UploadFile, File, Form
from infrastructure.auth_middleware import verify_firebase_token
import json

from typing import List

router = APIRouter(prefix="/expenses", tags=["Expense"])

@router.get("", response_model=List[ExpenseOut])
def list_expense(user_claims: dict = Depends(verify_firebase_token)):
    """
    List expenses. Employees see only their own, admins see all.
    """
    firebase_uid = user_claims.get("uid")
    
    # Get employee to determine role and internal ID
    employee = employee_service.get_employee_by_auth_id(firebase_uid)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    
    all_expenses = expense_service.list_expenses()
    
    # Filter based on role
    if employee.get("role") == "admin":
        return all_expenses
    else:
        # Return only this employee's expenses (match by internal employee_id)
        employee_id = employee.get("employee_id")
        return [exp for exp in all_expenses if exp.get("employee_id") == employee_id]


@router.post("", response_model=ExpenseOut)
async def create_expense(
    expense_data: str = Form(...),
    receipt: UploadFile = File(...),
    user_claims: dict = Depends(verify_firebase_token)
):
    """
    Create an expense. The employee_id is determined from the authenticated user,
    not from the request body (security).
    """
    firebase_uid = user_claims.get("uid")
    
    # Get employee to get internal employee_id
    employee = employee_service.get_employee_by_auth_id(firebase_uid)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    
    employee_id = employee.get("employee_id")
    
    # Parse expense data
    data_dict = json.loads(expense_data)
    
    # SECURITY: Override any employee_id from client with authenticated user's ID
    data_dict["employee_id"] = employee_id
    
    expense_create = ExpenseCreate(**data_dict)
    
    # Create expense with file handling
    return await expense_service.create_expense_with_file(expense_create, receipt)

@router.get("/{expense_id}", response_model=ExpenseOut)
def get_expense(expense_id: str):
    exp = expense_service.get_expense(expense_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")
    return exp

@router.patch("/{expense_id}", response_model=ExpenseOut)
def update_expense(expense_id: str, data: ExpenseUpdate):
    return expense_service.update_expense(expense_id, data.model_dump(exclude_unset=True))

@router.delete("/{expense_id}")
def delete_expense(expense_id: str):
    return expense_service.delete_expense(expense_id)
