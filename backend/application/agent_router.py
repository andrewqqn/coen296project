from fastapi import APIRouter
from domain.services import email_agent_service, expense_agent_service, document_agent_service
router = APIRouter(prefix="/agents", tags=["Agents"])
@router.post("/email/send")
def send_email_agent(payload: dict):
    return email_agent_service.send_notification(
        payload.get("to"),
        payload.get("subject", "Expense Notification"),
        payload.get("body", "")
    )
@router.post("/expense/review")
def review_expense_agent(expense: dict):
    return expense_agent_service.ai_review_expense(expense)
@router.post("/document/analyze")
def analyze_document_agent(payload: dict):
    return document_agent_service.analyze_receipt_text(payload.get("text", ""))
