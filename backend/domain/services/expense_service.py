from domain.repositories import expense_repo
from domain.repositories import document_repo
from domain.schemas.expense_schema import ExpenseCreate, ExpenseOut
from uuid import uuid4
from datetime import datetime

from domain.repositories import expense_repo
from domain.services.document_service import upload_receipt
from domain.schemas.expense_schema import ExpenseCreate, ExpenseOut
from datetime import datetime


async def create_expense(expense_create: ExpenseCreate, receipt_file):
    """
    Create a new expense record with receipt upload and Firestore insertion.
    Business logic lives here (not repo).
    """

    # -----------------------------
    # Step 1 — Upload receipt file
    # -----------------------------
    file_name = f"{expense_create.employee_id}_{datetime.utcnow().timestamp()}_{receipt_file.filename}"
    file_data = await receipt_file.read()
    file_path = upload_receipt(file_name, file_data)

    # -----------------------------
    # Step 2 — Construct Firestore data
    # -----------------------------
    data = {
        "employee_id": expense_create.employee_id,
        "amount": expense_create.amount,
        "category": expense_create.category,
        "business_justification": expense_create.business_justification,
        "receipt_path": file_path,
        "status": "pending",
        "decision_type": None,
        "decision_reason": None,
        "submitted_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    # -----------------------------
    # Step 3 — Insert into Firestore (repo)
    # -----------------------------
    expense_id = expense_repo.create(data)

    # -----------------------------
    # Step 4 — (Future) trigger AI auto-review
    # TODO: (Future) trigger AI auto-review
    # -----------------------------
    # auto_decision = ai_service.evaluate_expense(expense_id)
    # update Firestore accordingly

    # -----------------------------
    # Step 5 — Return response
    # -----------------------------
    return ExpenseOut(
        expense_id=expense_id,
        status=data["status"],
        submitted_at=datetime.utcnow()
    )

def list_expenses():
    return expense_repo.get_all()

def get_expense(expense_id: str):
    return expense_repo.get(expense_id)

def update_expense(expense_id, data):
    return expense_repo.update(expense_id, data)

def delete_expense(expense_id):
    return expense_repo.delete(expense_id)
