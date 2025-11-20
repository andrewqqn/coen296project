from email_agent.services.email_parser import EmailParser
from email_agent.services.email_organizer import EmailOrganizer
from email_agent.gmail.gmail_client import GmailClient

class EmailService:
    def __init__(self, gmail_service):
        self.client = GmailClient(gmail_service)
        self.parser = EmailParser()
        self.organizer = EmailOrganizer(self.client)

    def send_email(self, raw_message):
        return self.gmail.service.users().messages().send(
            userId="me",
            body=raw_message
        ).execute()
    
    def list_unread(self):
        msgs = self.client.list_messages("is:unread")
        return msgs

    def get_and_parse(self, msg_id):
        raw = self.client.get_message(msg_id)
        return self.parser.parse_message(raw)

    def organize(self, parsed_msg):
        self.organizer.auto_sort(parsed_msg)