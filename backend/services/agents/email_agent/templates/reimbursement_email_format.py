# email_agent/templates.py

def render_expense_decision_email(expense) -> tuple[str, str]:
    subject = f"Your expense request #{expense.expense_id} was {expense.status.upper()}"

    body = f"""
Hello,

We reviewed your expense request.

Status: {expense.status.upper()}
Amount: ${expense.amount}
Category: {expense.category}
Description: {expense.description}

Decision Type: {expense.decision_type}
Reason: {expense.decision_reason or 'N/A'}
Reviewed By: {expense.reviewed_by or 'Automated System'}

Submitted: {expense.submitted_at}
Updated: {expense.updated_at}

Thank you,
Expenditure Review Team
"""

    return subject, body
