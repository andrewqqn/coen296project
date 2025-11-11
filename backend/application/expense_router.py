from fastapi import APIRouter, HTTPException
from domain.services import expense_service
from domain.schemas.expense_schema import ExpenseCreate, ExpenseUpdate, ExpenseOut
from typing import List

router = APIRouter(prefix="/expenses", tags=["Expense"])

@router.get("", response_model=List[ExpenseOut])
def list_expense():
    return expense_service.list_expenses()

@router.post("", response_model=ExpenseOut)
def create_expense(data: ExpenseCreate):
    return expense_service.create_expense(data.dict())

@router.get("/{expense_id}", response_model=ExpenseOut)
def get_expense(expense_id: str):
    exp = expense_service.get_expense(expense_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")
    return exp

@router.patch("/{expense_id}", response_model=ExpenseOut)
def update_expense(expense_id: str, data: ExpenseUpdate):
    return expense_service.update_expense(expense_id, data.dict(exclude_unset=True))

@router.delete("/{expense_id}")
def delete_expense(expense_id: str):
    return expense_service.delete_expense(expense_id)
