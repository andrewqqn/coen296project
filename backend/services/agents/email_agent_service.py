from infrastructure.email_client import send_email
from utils.logger import get_logger
from services.audit_log_service import log_email_event

logger = get_logger(__name__)

def send_notification(to: str, subject: str, body: str, triggered_by: str = "system"):
    logger.info(f"Sending email to {to} ...")
    try:
        result = send_email(to, subject, body)
        success = result.get("status") == "sent"
        
        # Log email event
        log_email_event(
            to=to,
            subject=subject,
            triggered_by=triggered_by,
            success=success
        )
        
        return result
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        log_email_event(
            to=to,
            subject=subject,
            triggered_by=triggered_by,
            success=False
        )
        raise
