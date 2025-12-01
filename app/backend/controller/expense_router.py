from fastapi import APIRouter, HTTPException, Depends
from services import expense_service, employee_service
from domain.schemas.expense_schema import (ExpenseCreate, ExpenseOut, ExpenseUpdate)
from fastapi import UploadFile, File, Form
from infrastructure.auth_middleware import verify_firebase_token
import json
import logging

from typing import List

logger = logging.getLogger(__name__)

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
    
    # Update expense (this will automatically log the status change via expense_service)
    update_data = {
        "status": "approved" if action == "approve" else "rejected",
        "decision_actor": "Human",
        "decision_reason": reason
    }
    
    result = expense_service.update_expense(expense_id, update_data)
    
    # If approved, process payment
    if action == "approve":
        try:
            from services import financial_service
            from services.audit_log_service import log_payment_event
            
            # Get employee to find their bank account
            expense_employee_id = expense.get('employee_id')
            expense_employee = employee_service.get_employee(expense_employee_id)
            
            if expense_employee and expense_employee.get('bank_account_id'):
                bank_account_id = expense_employee['bank_account_id']
                expense_amount = float(expense.get('amount', 0))
                
                # Get current balance
                current_balance = financial_service.get_account_balance(bank_account_id)
                if current_balance is not None:
                    # Add expense amount to balance
                    new_balance = current_balance + expense_amount
                    financial_service.update_account_balance(bank_account_id, new_balance)
                    
                    # Log payment event
                    log_payment_event(
                        expense_id=expense_id,
                        employee_id=expense_employee_id,
                        amount=expense_amount,
                        bank_account_id=bank_account_id,
                        old_balance=current_balance,
                        new_balance=new_balance
                    )
        except Exception as e:
            logger.error(f"Failed to process payment for approved expense: {str(e)}")
    
    # Send email notification to employee
    try:
        import asyncio
        import threading
        from services.agents.email_agent_service import email_agent
        from services.agents.a2a_protocol import A2ARequest, create_a2a_message
        
        # Get employee email
        expense_employee_id = expense.get('employee_id')
        expense_employee = employee_service.get_employee(expense_employee_id)
        
        if expense_employee and expense_employee.get('email'):
            employee_email = expense_employee['email']
            
            # Create email notification request
            email_request = A2ARequest(
                capability_name="send_expense_notification",
                parameters={
                    "to": employee_email,
                    "expense_id": expense_id,
                    "status": "approved" if action == "approve" else "rejected",
                    "amount": float(expense.get('amount', 0)),
                    "category": expense.get('category', 'N/A'),
                    "decision_reason": f"Manual Review: {reason}"
                },
                context={"user_id": "admin", "role": "admin"}
            )
            
            # Send via A2A protocol
            message = create_a2a_message(
                sender_id="admin_review",
                recipient_id="email_agent",
                message_type="request",
                payload=email_request.model_dump(),
                capability_name="send_expense_notification"
            )
            
            # Send email notification in a separate thread to avoid blocking
            def send_notification_sync():
                try:
                    # Create new event loop for this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    response = loop.run_until_complete(
                        email_agent.process_message(
                            message,
                            context={"user_id": "admin", "role": "admin"}
                        )
                    )
                    
                    if response.message_type == "response":
                        logger.info(f"[EMAIL] Manual review notification sent to {employee_email} for expense {expense_id}")
                    else:
                        logger.warning(f"[EMAIL] Notification failed: {response.payload.get('error')}")
                    
                    loop.close()
                except Exception as e:
                    logger.error(f"[EMAIL] Failed to send notification: {str(e)}", exc_info=True)
            
            # Run in background thread (don't block the response)
            thread = threading.Thread(target=send_notification_sync, daemon=True)
            thread.start()
            logger.info(f"[EMAIL] Notification queued for {employee_email} about expense {expense_id}")
        else:
            logger.warning(f"[EMAIL] Could not send notification - employee has no email")
            
    except Exception as e:
        # Don't fail the review if email fails
        logger.error(f"[EMAIL] Failed to queue notification: {str(e)}", exc_info=True)
    
    return result


@router.get("/{expense_id}/receipt-url")
def get_receipt_url(
    expense_id: str,
    user_claims: dict = Depends(verify_firebase_token)
):
    """
    Get a signed URL to view/download the receipt for an expense.
    Employees can only access their own receipts, admins can access all.
    """
    firebase_uid = user_claims.get("uid")
    
    # Get employee to determine role and internal ID
    employee = employee_service.get_employee_by_auth_id(firebase_uid)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    
    # Get the expense
    expense = expense_service.get_expense(expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    # Check authorization: employees can only view their own receipts
    if employee.get("role") != "admin" and expense.get("employee_id") != employee.get("employee_id"):
        raise HTTPException(status_code=403, detail="Not authorized to view this receipt")
    
    # Check if receipt exists
    receipt_path = expense.get("receipt_path")
    if not receipt_path:
        raise HTTPException(status_code=404, detail="No receipt attached to this expense")
    
    # Generate signed URL
    url = expense_service.get_receipt_url(receipt_path)
    return {"url": url, "receipt_path": receipt_path}
