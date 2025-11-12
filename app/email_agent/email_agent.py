import re
import json
import time
import threading
import uuid
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Callable, Optional
import os


# # Optional LLM integration
# USE_OPENAI = bool(os.getenv("OPENAI_API_KEY"))
# if USE_OPENAI:
#     try:
#         import openai
#         openai.api_key = os.getenv("OPENAI_API_KEY")
#     except Exception as e:
#         print("OpenAI import failed:", e)
#         USE_OPENAI = False


# Data Models

@dataclass
class Email:
    message_id: str
    from_address: str
    to_address: str
    subject: str
    body: str
    attachments: List[Dict[str, Any]]
    

# @dataclass
# class ExpenseRequestEvent:



# Simple In-memory Event Bus
class EventBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}

    def subscribe(self, event_name: str, handler: Callable[[Dict[str, Any]], None]):
        self.subscribers.setdefault(event_name, []).append(handler)

    def publish(self, event_name: str, payload: Dict[str, Any]):
        print(f"[EventBus] Publishing: {event_name} -> {json.dumps(payload, default=str)}")
        handlers = self.subscribers.get(event_name, [])
        for h in handlers:
            # run handlers synchronously for simplicity
            try:
                h(payload)
            except Exception as e:
                print(f"[EventBus] Handler error for {event_name}: {e}")


class EmailAdapter:
    def list_unread(self) -> List[Email]:
        raise NotImplementedError

    def get_message(self, message_id: str) -> Email:
        raise NotImplementedError

    def send_message(self, to: str, subject: str, body: str, in_reply_to: Optional[str] = None):
        raise NotImplementedError


class EmailParser:
    AMOUNT_RE = re.compile(r"\$?([0-9]+(?:\.[0-9]{1,2})?)")
    DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")  # yyyy-mm-dd format if provided

    def parse_for_expense(email: Email):
        text = f"{email.subject}\n{email.body}".lower()
        expense_keywords = ["expense", "receipt", "reimbursement", "claim", "taxi", "uber", "flight", "hotel"]

        if not any(keyword in text for keyword in expense_keywords):
            return None
        
        money = self.AMOUNT_RE.search(email.body)
        amount = float(m.group(1)) if money else None

        d = self.DATE_RE.search(email.body)
        date = d.group(1) if d else time.strftime("%Y-%m-%d")

        return {"amount": amount or 0.0, "currency": "USD", "date": date}


class EmailClassifier:
    # Placeholder
    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm and USE_OPENAI
    
    def classify(self, email: Email) -> str:
        parser = EmailParser()
        expense = parser.parse_for_expense(email)

        if expense:
            # if any keywords for expense, treat as expense submission
            return "expense_submission"

        # if policy keywords, treat as policy query
        if "policy" in email.subject.lower() or "reimbursement policy" in email.body.lower():
            return "policy_query"

        # # fallback: if LLM available, ask it (careful: for prototyping only)
        # if self.use_llm:
        #     try:
        #         prompt = (
        #             "Classify the following email into one of: expense_submission, policy_query, general.\n\n"
        #             f"Subject: {email.subject}\n\nBody:\n{email.body}\n\nAnswer with only the label."
        #         )
        #         resp = openai.Completion.create(
        #             engine="text-davinci-003",
        #             prompt=prompt,
        #             max_tokens=8,
        #             temperature=0.0,
        #         )
        #         label = resp.choices[0].text.strip()
        #         if label in ("expense_submission", "policy_query", "general"):
        #             return label
        #     except Exception as e:
        #         print("[IntentClassifier] LLM call failed:", e)

        return "general"

    
class EmailAgent:
    def __init__(self, adapter: EmailAdapter, event_bus: EventBus) -> None:
        self.adapter = adapter
        self.event_bus = event_bus
        self.parser = EmailParser()
        self.classifier = EmailClassifier()
        self.read_emails = set()

    def process_inbound_emails(self, msg: Email):
        # Classify intent of message
        intent = self.classifier.classify(msg)
        print(f"Intent according to cliassifier: {intent}")

        if intent == "expense_submission":
            parsed = self.parser.parse_for_expense(msg)

            # Expense Event
            # event = 

            # Acknowledge receipt via email
            ack_body = (
                f"Hi,\n\nThanks — we received your expense submission for $.\n"
                f"Request ID: \n\n"
                "An Expense Agent will process this and you'll be notified about approval/denial.\n\nRegards,\nEnterprise Copilot (email agent)"
            )

            # Publish to event bus
            self.event_bus.publish("expense.request.submitted", asdict(event))

        elif intent == "policy_query":
            reply = "Please refer to company policies."
            self.adapter.send_message(to=msg.from_address, subject=f"Re: {msg.subject}", body=reply, in_reply_to=msg.message_id)

        else:
            # General reply
            reply = "AI cannot tell if this is expense or policy, so here's a generic reply."
            self.adapter.send_message(to=msg.from_address, subject=f"Re: {msg.subject}", body=reply, in_reply_to=msg.message_id)


    def process_unread(self):
        messages = self.adapter.list_unread()
        if not messages:
            print("No unread messages.")
            return
        
        for msg in messages:
            if msg.message_id in self.read_emails:
                continue

            print(f"Processing message {msg.message_id} from {msg.from_address}")
            try:
                self.process_inbound_email(msg)
            except Exception as e:
                print(f"Error processing {msg.message_id}: {e}")
            self.read_emails.add(msg.message_id)