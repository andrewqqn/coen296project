from infrastructure.email_client import send_email
from utils.logger import get_logger
logger = get_logger(__name__)
def send_notification(to: str, subject: str, body: str):
    logger.info(f"Sending email to {to} ...")
    return send_email(to, subject, body)
