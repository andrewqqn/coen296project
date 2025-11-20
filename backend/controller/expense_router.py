from fastapi import APIRouter, HTTPException
from services import expense_service
from domain.schemas.expense_schema import (ExpenseCreate, ExpenseOut, ExpenseUpdate)
from fastapi import UploadFile, File, Form
import json

from typing import List

router = APIRouter(prefix="/expenses", tags=["Expense"])

@router.get("", response_model=List[ExpenseOut])
def list_expense():
    return expense_service.list_expenses()


@router.post("", response_model=ExpenseOut)
async def create_expense(
    expense_data: str = Form(...),       # JSON as string
    receipt: UploadFile = File(...),     # file
):
    # Step 1: parse JSON string → Pydantic
    data_dict = json.loads(expense_data)
    expense_create = ExpenseCreate(**data_dict)

    # Step 2: send to service
    return await expense_service.create_expense(expense_create, receipt)

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
