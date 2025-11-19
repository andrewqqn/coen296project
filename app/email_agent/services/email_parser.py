import base64
from email import message_from_bytes


class EmailParser:
    
    @staticmethod
    def extract_body(msg) -> str:
        parts = msg.get("payload", {}).get("parts", [])

        for part in parts:
            if part["mimeType"] == "text/plain":
                data = part["body"]["data"]
                decoded = base64.urlsafe_b64decode(data).decode("utf-8")
                return decoded
        
        return ""
    
    @staticmethod
    def parse_message(msg) -> dict:
        body = EmailParser.extract_body(msg)
        headers = msg.get("payload", {}).get("headers", [])

        header_dict = {h["name"]: h["value"] for h in headers}

        return {
            "id": msg["id"],
            "subject": header_dict.get("Subject"),
            "from": header_dict.get("From"),
            "date": header_dict.get("Date"),
            "body": body,
        }