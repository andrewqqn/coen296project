from email.mime.text import MIMEText
from email.utils import formataddr
import base64


class EmailService:
    def __init__(self, gmail_client):
        self.client = gmail_client
        self.sender_email = gmail_client.get_authenticated_user_email()

    def send_email(self, to, subject, body):
        """
        Build RFC-2822 MIME email and let GmailClient send it.
        """
        if not self.sender_email:
            raise Exception("Authenticated Gmail user email not available")

        message = MIMEText(body)
        message["To"] = to
        message["From"] = formataddr(("Enterprise Copilot", self.sender_email))
        message["Subject"] = subject

        raw_message = {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}

        # Delegate to GmailClient
        return self.client.send_email(raw_message)

    def search_inbox(self, query=""):
        return self.client.list_messages(query=query)

    def read_message(self, message_id):
        return self.client.get_message(message_id)

    def add_label(self, message_id, label):
        return self.client.modify_labels(message_id, add_labels=[label])
