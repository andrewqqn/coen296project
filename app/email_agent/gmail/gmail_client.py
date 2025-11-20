from email.mime.text import MIMEText
import base64
from googleapiclient.discovery import build

class GmailClient:
    def __init__(self, service):
        self.service = service

    def get_authenticated_user_email(service):
        profile = service.users().getProfile(userId="me").execute()
        return profile["emailAddress"]

    def send_email(self, sender, to, subject, body):
        message = MIMEText(body)
        message["to"] = to
        message["from"] = sender
        message["subject"] = subject

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        payload = {"raw": raw_message}

        return self.service.users().messages().send(
            userId="me",
            body=payload
        ).execute()
    
    def list_messages(self, query=""):
        return self.service.users().messages().list(
            userId="me",
            q=query
        ).execute().get("messages", [])

    def get_message(self, msg_id):
        return self.service.users().messages().get(
            userId="me",
            id=msg_id,
            format="full"
        ).execute()

    def list_labels(self):
        return self.service.users().labels().list(
            userId="me"
        ).execute().get("labels", [])

    def modify_labels(self, msg_id, add=None, remove=None):
        body = {
            "addLabelIds": add or [],
            "removeLabelIds": remove or []
        }
        return self.service.users().messages().modify(
            userId="me",
            id=msg_id,
            body=body
        ).execute()
