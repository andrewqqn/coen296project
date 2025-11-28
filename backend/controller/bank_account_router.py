from fastapi import APIRouter, HTTPException, Depends
from services import financial_service
from typing import Optional
from utils.auth import get_current_user

router = APIRouter(prefix="/bank-accounts", tags=["Bank Account"])


@router.get("/me")
def get_my_bank_account(current_user: dict = Depends(get_current_user)):
    """Get the current authenticated user's bank account"""
    from services import employee_service
    from infrastructure.firebase_client import get_firestore_client
    import uuid
    
    # Get employee profile to find employee_id
    emp = employee_service.get_employee_by_auth_id(current_user["uid"])
    if emp is None:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    
    employee_id = emp.get("employee_id")
    bank_account_id = emp.get("bank_account_id")
    
    # If employee has a bank_account_id, fetch it directly
    if bank_account_id:
        account = financial_service.get_bank_account(bank_account_id)
        if account:
            account["bank_account_id"] = bank_account_id
            return account
    
    # Otherwise, try to find by employee_id (for backwards compatibility)
    db = get_firestore_client()
    accounts = db.collection("bank_accounts").where("employee_id", "==", employee_id).limit(1).stream()
    
    for doc in accounts:
        account_data = doc.to_dict()
        account_data["bank_account_id"] = doc.id
        # Ensure balance has 2 decimal precision
        if "balance" in account_data:
            account_data["balance"] = round(float(account_data["balance"]), 2)
        
        # Update employee record with the bank_account_id for future lookups
        employee_service.update_employee(employee_id, {"bank_account_id": doc.id})
        
        return account_data
    
    # If no bank account exists, create one automatically
    bank_account_id = str(uuid.uuid4())
    bank_account_data = {
        "holder_name": emp.get("name", "Unknown"),
        "email": emp.get("email", ""),
        "employee_id": employee_id,
        "balance": 0.0
    }
    financial_service.create_bank_account(bank_account_id, bank_account_data)
    
    # Update employee with bank_account_id
    employee_service.update_employee(employee_id, {"bank_account_id": bank_account_id})
    
    return {
        "bank_account_id": bank_account_id,
        "holder_name": bank_account_data["holder_name"],
        "email": bank_account_data["email"],
        "employee_id": employee_id,
        "balance": 0.0
    }


@router.get("/{bank_account_id}")
def get_bank_account(bank_account_id: str):
    """Get bank account by ID"""
    account = financial_service.get_bank_account(bank_account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Bank account not found")
    account["bank_account_id"] = bank_account_id
    return account
