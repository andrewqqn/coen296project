# from google.oauth2.credentials import Credentials
# from googleapiclient.discovery import build

# creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/gmail.modify"])
# service = build("gmail", "v1", credentials=creds)

import base64
from email.mime.text import MIMEText

def send_email(service, to, subject, body):
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    encoded_msg = base64.urlsafe_b64encode(message.as_bytes()).decode()

    send_result = service.users().messages().send(userId = "me", body = {"raw": encoded_msg}).execute()
    print("Email sent:", send_result["id"])


def read_latest_emails(service, max_results = 5):
    results = service.users().messages().list(userId = "me", maxResults = max_results).execute()
    messages = results.get("messages", [])

    for msg in messages:
        email_data = service.users().messages().get(userId = "me", id = msg["id"], format = "full").execute()
        snippet = email_data["snippet"]
        print("Subject:", snippet)


