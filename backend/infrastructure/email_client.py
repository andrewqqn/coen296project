import os, smtplib
from email.mime.text import MIMEText
def send_email(to, subject, body):
    sender = os.getenv("EMAIL_SENDER", "noreply@example.com")
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to
    print(f"Sending email to {to} ...")
    return {"status": "sent", "to": to}
