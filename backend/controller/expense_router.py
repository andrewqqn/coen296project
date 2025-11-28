from fastapi import APIRouter, HTTPException, Depends
from services import expense_service, employee_service
from domain.schemas.expense_schema import (ExpenseCreate, ExpenseOut, ExpenseUpdate)
from fastapi import UploadFile, File, Form
from infrastructure.auth_middleware import verify_firebase_token
import json

from typing import List

router = APIRouter(prefix="/expenses", tags=["Expense"])

@router.get("")
def list_expense(user_claims: dict = Depends(verify_firebase_token)):
    """
    List expenses. Employees see only their own, admins see all.
    For admins, includes employee information (name, email) for each expense.
    """
    firebase_uid = user_claims.get("uid")
    
    # Get employee to determine role and internal ID
    employee = employee_service.get_employee_by_auth_id(firebase_uid)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    
    all_expenses = expense_service.list_expenses()
    
    # Filter based on role
    if employee.get("role") == "admin":
        # For admins, enrich expenses with employee information
        enriched_expenses = []
        for exp in all_expenses:
            expense_dict = dict(exp) if not isinstance(exp, dict) else exp
            emp_id = expense_dict.get("employee_id")
            if emp_id:
                emp_data = employee_service.get_employee(emp_id)
                if emp_data:
                    expense_dict["employee_name"] = emp_data.get("name", "Unknown")
                    expense_dict["employee_email"] = emp_data.get("email", "Unknown")
            enriched_expenses.append(expense_dict)
        return enriched_expenses
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


@router.post("/{expense_id}/review", response_model=ExpenseOut)
def review_expense(
    expense_id: str,
    action: str = Form(...),  # "approve" or "reject"
    reason: str = Form(...),
    user_claims: dict = Depends(verify_firebase_token)
):
    """
    Admin-only endpoint to approve or reject expenses in admin_review status.
    """
    firebase_uid = user_claims.get("uid")
    
    # Get employee to verify admin role
    employee = employee_service.get_employee_by_auth_id(firebase_uid)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    
    if employee.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can review expenses")
    
    # Get the expense
    expense = expense_service.get_expense(expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    # Verify it's in admin_review status
    if expense.get("status") != "admin_review":
        raise HTTPException(
            status_code=400, 
            detail=f"Expense is not in admin_review status (current: {expense.get('status')})"
        )
    
    # Validate action
    if action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")
    
    # Update expense
    update_data = {
        "status": "approved" if action == "approve" else "rejected",
        "decision_actor": "Human",
        "decision_reason": reason
    }
    
    return expense_service.update_expense(expense_id, update_data)
