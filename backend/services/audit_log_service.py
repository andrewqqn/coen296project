from domain.repositories import audit_log_repo
from datetime import datetime
from typing import Literal

def list_logs(): 
    return audit_log_repo.get_all()

def create_log(data): 
    """Create an audit log entry with timestamp"""
    if "timestamp" not in data:
        data["timestamp"] = datetime.utcnow()
    return audit_log_repo.create(data)

def log_expense_status_change(
    actor: Literal["AI", "Human"],
    expense_id: str,
    old_status: str,
    new_status: str,
    reason: str = ""
):
    """Log expense status changes (approve, reject, admin-review)"""
    return create_log({
        "actor": actor,
        "log": f"Expense {expense_id} status changed: {old_status} → {new_status}. Reason: {reason}",
        "expense_id": expense_id,
        "event_type": "expense_status_change",
        "old_status": old_status,
        "new_status": new_status,
        "reason": reason
    })

def log_inter_agent_message(
    from_agent: str,
    to_agent: str,
    capability: str,
    parameters: dict,
    success: bool = True,
    error: str = None
):
    """Log inter-agent communication"""
    log_msg = f"Agent message: {from_agent} → {to_agent}.{capability}"
    if not success:
        log_msg += f" [FAILED: {error}]"
    
    return create_log({
        "actor": "AI",
        "log": log_msg,
        "event_type": "inter_agent_message",
        "from_agent": from_agent,
        "to_agent": to_agent,
        "capability": capability,
        "parameters": parameters,
        "success": success,
        "error": error
    })

def log_unauthorized_access(
    actor: Literal["AI", "Human"],
    user_id: str,
    resource: str,
    action: str,
    reason: str
):
    """Log unauthorized access attempts"""
    return create_log({
        "actor": actor,
        "log": f"Unauthorized access attempt: {user_id} tried to {action} {resource}. Reason: {reason}",
        "event_type": "unauthorized_access",
        "user_id": user_id,
        "resource": resource,
        "action": action,
        "reason": reason
    })

def log_payment_event(
    expense_id: str,
    employee_id: str,
    amount: float,
    bank_account_id: str,
    old_balance: float,
    new_balance: float
):
    """Log payment processing events"""
    return create_log({
        "actor": "AI",
        "log": f"Payment processed: ${amount} for expense {expense_id} to account {bank_account_id}. Balance: ${old_balance} → ${new_balance}",
        "event_type": "payment_event",
        "expense_id": expense_id,
        "employee_id": employee_id,
        "amount": amount,
        "bank_account_id": bank_account_id,
        "old_balance": old_balance,
        "new_balance": new_balance
    })

def log_email_event(
    to: str,
    subject: str,
    triggered_by: str,
    success: bool = True
):
    """Log email sending events"""
    status = "sent" if success else "failed"
    return create_log({
        "actor": "AI",
        "log": f"Email {status}: to={to}, subject={subject}, triggered_by={triggered_by}",
        "event_type": "email_event",
        "to": to,
        "subject": subject,
        "triggered_by": triggered_by,
        "success": success
    })
