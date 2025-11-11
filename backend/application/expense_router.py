from fastapi import APIRouter, HTTPException
from infrastructure.auth_middleware import verify_firebase_token
from domain.services import expense_service
router = APIRouter(prefix="/expenses", tags=["Expense"])
@router.get("")
def list_expense():
    return expense_service.list_expenses()
@router.post("")
def create_expense(data: dict):
    return expense_service.create_expense(data)
@router.get("/{expense_id}")
def get_expense(expense_id: str):
    exp = expense_service.get_expense(expense_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")
    return exp
@router.patch("/{expense_id}")
def update_expense(expense_id: str, data: dict):
    return expense_service.update_expense(expense_id, data)
@router.delete("/{expense_id}")
def delete_expense(expense_id: str):
    return expense_service.delete_expense(expense_id)
