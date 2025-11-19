from domain.repositories import expense_repo
from services.document_service import upload_receipt
from domain.schemas.expense_schema import ExpenseCreate, ExpenseOut
from datetime import datetime
from services.agents.expense_agent_service import auto_review_on_create


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
    receipt_path = upload_receipt(file_name, file_data)
    file_path = receipt_path["path"]

    # -----------------------------
    # Step 2 — Construct Firestore data
    # -----------------------------
    data = {
        "employee_id": expense_create.employee_id,
        "date_of_expense": expense_create.date_of_expense,
        "amount": expense_create.amount,
        "category": expense_create.category,
        "business_justification": expense_create.business_justification,
        "receipt_path": file_path,
        "status": "pending",
        "decision_type": "",
        "decision_reason": "",
        "submitted_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    # -----------------------------
    # Step 3 — Insert into Firestore (repo)
    # -----------------------------
    expense_id = expense_repo.create(data)

    # # -----------------------------
    # # Step 4 — (Future) trigger AI auto-review
    #
    # # -----------------------------
    auto_review_on_create(expense_id=expense_id)

    # -----------------------------
    # Step 5 — Return response
    # -----------------------------
    return ExpenseOut(
        expense_id=expense_id,
        date_of_expense=expense_create.date_of_expense,
        employee_id=data["employee_id"],
        amount=data["amount"],
        business_justification=data["business_justification"],
        category=data["category"],
        status="pending",
        decision_actor="",
        decision_reason="",

        receipt_path=data["receipt_path"],
        submitted_at=data["submitted_at"],
        updated_at=data["updated_at"],
    )

def list_expenses():
    return expense_repo.get_all()

def get_expense(expense_id: str):
    return expense_repo.get(expense_id)

def update_expense(expense_id: str, data: dict):
    data = data.copy()
    data["updated_at"] = datetime.utcnow().isoformat()
    return expense_repo.update(expense_id, data)

def delete_expense(expense_id):
    return expense_repo.delete(expense_id)
