from email.mime.text import MIMEText
import base64
from email_agent.services.email_parser import EmailParser


def test_parse_mime_message():
    parser = EmailParser()

    msg = MIMEText("Hello world")
    msg["Subject"] = "Test subject"
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    result = parser.parse_raw_email({"raw": raw})

    assert result["subject"] == "Test subject"
    assert result["body"] == "Hello world"
