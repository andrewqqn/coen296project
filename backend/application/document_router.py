from fastapi import APIRouter, HTTPException
from domain.services import document_service
from domain.repositories import expense_repo

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/receipt/{expense_id}")
def get_receipt_url(expense_id: str):
    """
    Generate a temporary URL to view the receipt for a given expense.
    Admin UI uses this to show PDF.
    """
    expense = expense_repo.get(expense_id)
    if not expense:
        raise HTTPException(404, "Expense not found")

    file_path = expense.get("receipt_path")
    if not file_path:
        raise HTTPException(404, "Receipt not found for this expense")

    url = document_service.generate_receipt_url(file_path)
    return {"expense_id": expense_id, "url": url}
