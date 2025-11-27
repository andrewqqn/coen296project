import base64
import logging
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class GmailClient:
    def __init__(self, service):
        self.service = service

    def get_authenticated_user_email(self, user_id="me"):
        try:
            profile = self.service.users().getProfile(userId=user_id).execute()
            return profile.get("emailAddress")
        except HttpError as e:
            logger.error(f"Gmail API error getting user profile: {e}")
            return None

    def send_email(self, raw_message, user_id="me"):
        """Send a raw RFC-2822 encoded email body."""
        try:
            result = (
                self.service.users()
                .messages()
                .send(userId=user_id, body=raw_message)
                .execute()
            )
            return result
        except HttpError as e:
            logger.error(f"Gmail send_email error: {e}")
            raise
    
    def list_messages(self, query="", user_id="me", max_results=50):
        try:
            response = (
                self.service.users()
                .messages()
                .list(userId=user_id, q=query, maxResults=max_results)
                .execute()
            )
            return response.get("messages", [])
        except HttpError as e:
            logger.error(f"Gmail list_messages error: {e}")
            return []

    def get_message(self, message_id, user_id="me"):
        try:
            return (
                self.service.users()
                .messages()
                .get(userId=user_id, id=message_id, format="full")
                .execute()
            )
        except HttpError as e:
            logger.error(f"Gmail get_message error: {e}")
            return None

    def modify_labels(self, message_id, add_labels=None, remove_labels=None, user_id="me"):
        try:
            payload = {
                "addLabelIds": add_labels or [],
                "removeLabelIds": remove_labels or []
            }
            return (
                self.service.users()
                .messages()
                .modify(userId=user_id, id=message_id, body=payload)
                .execute()
            )
        except HttpError as e:
            logger.error(f"Gmail modify_labels error: {e}")
            return None
