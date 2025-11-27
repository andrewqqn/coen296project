import base64
import email

class EmailParser:
    def parse_raw_email(self, gmail_message):
        """Parse raw MIME email from Gmail API format"""
        raw_data = gmail_message.get("raw", "")
        decoded = base64.urlsafe_b64decode(raw_data)
        msg = email.message_from_bytes(decoded)
        
        return {
            "subject": msg.get("Subject", ""),
            "from": msg.get("From", ""),
            "to": msg.get("To", ""),
            "body": self._extract_body(msg)
        }
    
    def _extract_body(self, msg):
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    return part.get_payload(decode=True).decode()
        else:
            return msg.get_payload(decode=True).decode()
