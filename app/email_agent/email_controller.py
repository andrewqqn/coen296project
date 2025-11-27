from backend.domain.models.expense import Expense
from .services import EmailService
from .templates import render_expense_decision_email

class EmailController:
    
    def __init__(self, event_bus, email_service: EmailService):
        self.event_bus = event_bus
        self.email_service = email_service

        # self.event_bus.subscribe("expense.status.changed", self.handle_status_change)
        self.event_bus.subscribe("email.send", self.handle_send_email)
        self.event_bus.subscribe("email.search", self.handle_search_email)

    def handle_status_change(self, payload):
        exp_dict = payload["expense"]
        employee_email = payload["employee_email"]

        # Reconstruct domain object
        expense = Expense(**exp_dict)

        subject, body = render_expense_decision_email(expense)

        self.email_service.send_email(
            to=employee_email,
            subject=subject,
            body=body
        )

    def handle_send_email(self, payload):
        self.email_service.send_email(
            to=payload["to"],
            subject=payload["subject"],
            body=payload["body"]
        )

    def handle_search_email(self, payload):
        query = payload.get("query", "")
        return self.email_service.client.list_messages(query)