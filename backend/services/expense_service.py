from domain.repositories import expense_repo
from services.document_service import upload_receipt, generate_receipt_url
from domain.schemas.expense_schema import ExpenseCreate, ExpenseOut
from datetime import datetime
from services.agents.expense_agent_service import auto_review_on_create


def create_expense(expense_create: ExpenseCreate, receipt_path: str = None):
    """
    Create a new expense record with optional receipt path.
    Business logic lives here (not repo).
    
    Args:
        expense_create: Expense data
        receipt_path: Optional path to already-uploaded receipt in storage
    """
    # Construct Firestore data
    data = {
        "employee_id": expense_create.employee_id,
        "date_of_expense": expense_create.date_of_expense,
        "amount": expense_create.amount,
        "category": expense_create.category,
        "business_justification": expense_create.business_justification,
        "receipt_path": receipt_path,
        "status": "pending",
        "decision_reason": "",
        "submitted_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    # Insert into Firestore
    expense_id = expense_repo.create(data)

    # Trigger AI auto-review if there's a receipt
    if receipt_path:
        auto_review_on_create(expense_id=expense_id)

    # Return response
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


async def create_expense_with_file(expense_create: ExpenseCreate, receipt_file):
    """
    Create expense with file upload handling.
    Used by REST API endpoint that accepts multipart/form-data.
    
    Args:
        expense_create: Expense data
        receipt_file: UploadFile object from FastAPI
    """
    # Upload receipt file
    file_name = f"{expense_create.employee_id}_{datetime.utcnow().timestamp()}_{receipt_file.filename}"
    file_data = await receipt_file.read()
    receipt_result = upload_receipt(file_name, file_data)
    receipt_path = receipt_result["path"]
    
    # Create expense with the uploaded receipt path
    return create_expense(expense_create, receipt_path=receipt_path)

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

def get_by_employee(employee_id: str):
    return expense_repo.get_by_employee(employee_id)

def get_receipt_url(receipt_path: str, expire_seconds: int = 3600):
    """
    Generate a signed URL for viewing/downloading a receipt.
    
    Args:
        receipt_path: Path to the receipt in storage
        expire_seconds: URL expiration time in seconds (default 1 hour)
    
    Returns:
        Signed URL string
    """
    return generate_receipt_url(receipt_path, expire_seconds)
